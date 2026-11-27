"""Repository operations backed by GitHub App installation tokens.

All calls are short GitHub REST requests, so they are safe on either Render or
Vercel. Every mutation is permission-checked, audited and optionally
idempotent so a retried request never creates a duplicate commit or PR.
"""

import base64
from typing import Any, Awaitable, Callable
from urllib.parse import quote

from fastapi import HTTPException, status

from app.core.auth import _is_admin
from app.schemas.repo_ops import (
    BranchCreateRequest,
    BranchListOut,
    BranchOut,
    CommitOut,
    CompareFileOut,
    CompareOut,
    ConfigApplyRequest,
    ConfigOut,
    ConfigPreviewOut,
    ConfigPreviewRequest,
    FileOut,
    FileWriteRequest,
    MergeOut,
    PullCreateRequest,
    PullListOut,
    PullOut,
    PullUpdateRequest,
    PullMergeRequest,
    RepoAuditListOut,
    RepoRoleListOut,
    TemplateListOut,
    TreeEntryOut,
    TreeListOut,
)
from app.services.customization import (
    CONFIG_PATH,
    builtin_templates,
    config_diff,
    default_config,
    dump_config,
    parse_config,
)
from app.services.github_app import GitHubAppService, get_github_app_service

MAX_TREE_ENTRIES = 1000
MAX_PATCH_CHARS = 20_000
MAX_FILE_CHARS = 500_000


class RepoOpsService:
    def __init__(self, github: GitHubAppService | None = None) -> None:
        self.github = github or get_github_app_service()

    @property
    def repo(self):
        return self.github.repo

    async def resolve(self, repository_id: str, user: dict, *, write: bool = False) -> dict:
        row = await self.repo.get_repository(repository_id)
        if not row:
            raise HTTPException(status_code=404, detail="Repository not found")
        await self.authorize(row, user, write=write)
        return row

    async def authorize(self, row: dict, user: dict, *, write: bool) -> None:
        user_id = str(user.get("sub") or "")
        if _is_admin(user):
            return
        role = await self.repo.get_role(str(row["id"]), user_id) if user_id else None
        allowed = role in (("owner", "write", "read") if not write else ("owner", "write"))
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this repository",
            )

    def _base_path(self, row: dict) -> str:
        full_name = str(row.get("full_name") or "")
        owner, separator, name = full_name.partition("/")
        if not separator:
            owner, name = "", owner
        return f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"

    @staticmethod
    def _file_path(path: str) -> str:
        cleaned = path.lstrip("/")
        return "/".join(quote(segment, safe="") for segment in cleaned.split("/"))

    async def _audit(
        self,
        row: dict,
        user: dict,
        action: str,
        *,
        target: str = "",
        detail: dict | None = None,
        request_id: str = "",
    ) -> None:
        await self.repo.add_audit(
            str(row["id"]),
            str(user.get("sub") or ""),
            action,
            target=target,
            detail=detail,
            request_id=request_id,
        )

    async def _cached(self, user: dict, key: str) -> dict | None:
        if not key:
            return None
        actor = str(user.get("sub") or "")
        row = await self.repo.get_idempotent(f"{actor}:{key}")
        return row.get("result") if row else None

    @staticmethod
    def _commit_out(result: dict, path: str, branch: str) -> CommitOut:
        if "commit_sha" in result:
            return CommitOut(**result)
        commit = result.get("commit") or {}
        content = result.get("content") or {}
        return CommitOut(
            commit_sha=str(commit.get("sha") or ""),
            path=path,
            branch=branch,
            content_url=str(content.get("html_url") or ""),
        )

    async def _mutation(
        self,
        *,
        row: dict,
        user: dict,
        key: str,
        action: str,
        target: str,
        detail: dict | None,
        request_id: str,
        work: Callable[[], Awaitable[dict]],
    ) -> dict:
        actor = str(user.get("sub") or "")
        cache_key = f"{actor}:{key}" if key else ""
        if cache_key:
            cached = await self.repo.get_idempotent(cache_key)
            if cached:
                return cached.get("result") or {}
        result = await work()
        if cache_key:
            await self.repo.record_idempotent(
                cache_key, actor, str(row["id"]), action, result
            )
        await self._audit(
            row,
            user,
            action,
            target=target,
            detail=detail,
            request_id=request_id,
        )
        return result

    # -- Branches -------------------------------------------------------------

    async def list_branches(self, repository_id: str, user: dict) -> BranchListOut:
        row = await self.resolve(repository_id, user)
        data = await self.github.request(
            int(row["installation_id"]),
            "GET",
            f"{self._base_path(row)}/branches",
            params={"per_page": 100},
        )
        items = data if isinstance(data, list) else []
        return BranchListOut(
            branches=[
                BranchOut(
                    name=str(item.get("name") or ""),
                    sha=str((item.get("commit") or {}).get("sha") or ""),
                    protected=bool(item.get("protected", False)),
                )
                for item in items
            ]
        )

    async def create_branch(
        self, repository_id: str, user: dict, payload: BranchCreateRequest, request_id: str = ""
    ) -> BranchOut:
        row = await self.resolve(repository_id, user, write=True)
        from_ref = payload.from_ref or str(row.get("default_branch") or "main")
        ref = await self.github.request(
            int(row["installation_id"]),
            "GET",
            f"{self._base_path(row)}/branches/{self.path_segment(from_ref)}",
        )
        sha = str(ref.get("commit", {}).get("sha") or "")
        if not sha:
            raise HTTPException(status_code=404, detail="Source branch has no commit SHA")
        name = payload.name.strip()
        await self._mutation(
            row=row,
            user=user,
            key=f"branch:{name}",
            action="branch.create",
            target=name,
            detail={"from_ref": from_ref},
            request_id=request_id,
            work=lambda: self.github.request(
                int(row["installation_id"]),
                "POST",
                f"{self._base_path(row)}/git/refs",
                json_body={"ref": f"refs/heads/{name}", "sha": sha},
            ),
        )
        return BranchOut(name=name, sha=sha, protected=False)

    async def delete_branch(
        self, repository_id: str, branch: str, user: dict, request_id: str = ""
    ) -> dict:
        row = await self.resolve(repository_id, user, write=True)
        return await self._mutation(
            row=row,
            user=user,
            key=f"branch-delete:{branch}",
            action="branch.delete",
            target=branch,
            detail=None,
            request_id=request_id,
            work=lambda: self.github.request(
                int(row["installation_id"]),
                "DELETE",
                f"{self._base_path(row)}/git/refs/heads/{self.path_segment(branch)}",
            ),
        ) or {"deleted": True, "branch": branch}

    # -- Files ----------------------------------------------------------------

    async def list_files(
        self, repository_id: str, user: dict, branch: str = "", path: str = ""
    ) -> TreeListOut:
        row = await self.resolve(repository_id, user)
        ref = branch or str(row.get("default_branch") or "main")
        data = await self.github.request(
            int(row["installation_id"]),
            "GET",
            f"{self._base_path(row)}/git/trees/{self.path_segment(ref)}",
            params={"recursive": "1"},
        )
        items = data.get("tree", []) if isinstance(data, dict) else []
        prefix = path.strip("/")
        entries = [
            TreeEntryOut(
                path=str(item.get("path") or ""),
                type=str(item.get("type") or "blob"),
                sha=str(item.get("sha") or ""),
                size=item.get("size"),
            )
            for item in items
            if not prefix or str(item.get("path") or "").startswith(f"{prefix}/")
        ]
        return TreeListOut(
            branch=ref,
            truncated=bool(data.get("truncated", False)) if isinstance(data, dict) else False,
            entries=entries[:MAX_TREE_ENTRIES],
        )

    async def _raw_file(
        self, row: dict, path: str, branch: str = "", *, required: bool = True
    ) -> dict | None:
        ref = branch or str(row.get("default_branch") or "main")
        try:
            data = await self.github.request(
                int(row["installation_id"]),
                "GET",
                f"{self._base_path(row)}/contents/{self._file_path(path)}",
                params={"ref": ref},
            )
        except HTTPException as exc:
            if not required and exc.status_code == 404:
                return None
            raise
        return data if isinstance(data, dict) else None

    async def get_file(
        self, repository_id: str, user: dict, path: str, branch: str = ""
    ) -> FileOut:
        row = await self.resolve(repository_id, user)
        ref = branch or str(row.get("default_branch") or "main")
        data = await self._raw_file(row, path, ref)
        if not data:
            raise HTTPException(status_code=404, detail="File not found")
        raw = str(data.get("content") or "")
        try:
            content = base64.b64decode(raw).decode("utf-8", errors="replace")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="File is not valid base64") from exc
        size = int(data.get("size") or len(content))
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS]
        return FileOut(
            path=path,
            branch=ref,
            content=content,
            sha=str(data.get("sha") or ""),
            size=size,
            truncated=len(content) < size,
        )

    async def write_file(
        self, repository_id: str, user: dict, payload: FileWriteRequest, request_id: str = ""
    ) -> CommitOut:
        row = await self.resolve(repository_id, user, write=True)
        branch = payload.branch or str(row.get("default_branch") or "main")
        key = payload.idempotency_key or f"file:{branch}:{payload.path}"
        cached = await self._cached(user, key)
        if cached is not None:
            return self._commit_out(cached, payload.path, branch)
        sha = payload.sha
        if not sha:
            existing = await self._raw_file(row, payload.path, branch, required=False)
            if existing:
                sha = str(existing.get("sha") or "")
        encoded = base64.b64encode(payload.content.encode("utf-8")).decode("ascii")

        async def work() -> dict:
            body: dict[str, Any] = {
                "message": payload.message,
                "content": encoded,
                "branch": branch,
            }
            if sha:
                body["sha"] = sha
            return await self.github.request(
                int(row["installation_id"]),
                "PUT",
                f"{self._base_path(row)}/contents/{self._file_path(payload.path)}",
                json_body=body,
            )

        result = await self._mutation(
            row=row,
            user=user,
            key=key,
            action="file.write",
            target=payload.path,
            detail={"branch": branch, "message": payload.message},
            request_id=request_id,
            work=work,
        )
        return self._commit_out(result, payload.path, branch)

    # -- Pull requests --------------------------------------------------------

    async def list_pulls(
        self, repository_id: str, user: dict, state: str = "open"
    ) -> PullListOut:
        row = await self.resolve(repository_id, user)
        data = await self.github.request(
            int(row["installation_id"]),
            "GET",
            f"{self._base_path(row)}/pulls",
            params={"state": state, "per_page": 100},
        )
        items = data if isinstance(data, list) else []
        return PullListOut(
            pulls=[
                PullOut(
                    number=int(item.get("number") or 0),
                    title=str(item.get("title") or ""),
                    state=str(item.get("state") or "open"),
                    head=str((item.get("head") or {}).get("ref") or ""),
                    base=str((item.get("base") or {}).get("ref") or ""),
                    url=str(item.get("html_url") or ""),
                    draft=bool(item.get("draft", False)),
                )
                for item in items
            ]
        )

    @staticmethod
    def _pull_body(data: dict) -> PullOut:
        return PullOut(
            number=int(data.get("number") or 0),
            title=str(data.get("title") or ""),
            state=str(data.get("state") or "open"),
            head=str((data.get("head") or {}).get("ref") or ""),
            base=str((data.get("base") or {}).get("ref") or ""),
            url=str(data.get("html_url") or ""),
            draft=bool(data.get("draft", False)),
        )

    async def create_pull(
        self, repository_id: str, user: dict, payload: PullCreateRequest, request_id: str = ""
    ) -> PullOut:
        row = await self.resolve(repository_id, user, write=True)
        base = payload.base or str(row.get("default_branch") or "main")
        key = payload.idempotency_key or f"pr:{payload.head}:{base}"
        cached = await self._cached(user, key)
        if cached is not None:
            return self._pull_body(cached)

        async def work() -> dict:
            return await self.github.request(
                int(row["installation_id"]),
                "POST",
                f"{self._base_path(row)}/pulls",
                json_body={
                    "title": payload.title,
                    "head": payload.head,
                    "base": base,
                    "body": payload.body,
                    "draft": payload.draft,
                },
            )

        result = await self._mutation(
            row=row,
            user=user,
            key=key,
            action="pull.create",
            target=f"{payload.head}->{base}",
            detail={"title": payload.title},
            request_id=request_id,
            work=work,
        )
        return self._pull_body(result)

    async def update_pull(
        self,
        repository_id: str,
        number: int,
        user: dict,
        payload: PullUpdateRequest,
        request_id: str = "",
    ) -> PullOut:
        row = await self.resolve(repository_id, user, write=True)
        body = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not body:
            raise HTTPException(status_code=400, detail="No changes supplied")
        result = await self._mutation(
            row=row,
            user=user,
            key="",
            action="pull.update",
            target=f"#{number}",
            detail={"fields": sorted(body)},
            request_id=request_id,
            work=lambda: self.github.request(
                int(row["installation_id"]),
                "PATCH",
                f"{self._base_path(row)}/pulls/{number}",
                json_body=body,
            ),
        )
        return self._pull_body(result)

    async def merge_pull(
        self,
        repository_id: str,
        number: int,
        user: dict,
        payload: PullMergeRequest,
        request_id: str = "",
    ) -> MergeOut:
        row = await self.resolve(repository_id, user, write=True)
        key = payload.idempotency_key or f"merge:{number}"
        cached = await self._cached(user, key)
        if cached is not None:
            return self._merge_out(cached)
        body = {
            "merge_method": payload.merge_method,
            "commit_title": payload.commit_title,
            "commit_message": payload.commit_message,
        }

        async def work() -> dict:
            return await self.github.request(
                int(row["installation_id"]),
                "PUT",
                f"{self._base_path(row)}/pulls/{number}/merge",
                json_body=body,
            )

        result = await self._mutation(
            row=row,
            user=user,
            key=key,
            action="pull.merge",
            target=f"#{number}",
            detail={"merge_method": payload.merge_method},
            request_id=request_id,
            work=work,
        )
        return self._merge_out(result)

    @staticmethod
    def _merge_out(result: dict) -> MergeOut:
        return MergeOut(
            merged=bool(result.get("merged", True)),
            sha=str(result.get("sha") or ""),
            message=str(result.get("message") or ""),
        )

    # -- Diffs ----------------------------------------------------------------

    async def compare(
        self, repository_id: str, user: dict, base: str, head: str
    ) -> CompareOut:
        row = await self.resolve(repository_id, user)
        default = str(row.get("default_branch") or "main")
        base = base or default
        head = head or default
        comparison = await self.github.request(
            int(row["installation_id"]),
            "GET",
            f"{self._base_path(row)}/compare/{self.path_segment(base)}...{self.path_segment(head)}",
        )
        files = [
            CompareFileOut(
                filename=str(item.get("filename") or ""),
                status=str(item.get("status") or ""),
                additions=int(item.get("additions") or 0),
                deletions=int(item.get("deletions") or 0),
                patch=str(item.get("patch") or "")[:MAX_PATCH_CHARS],
            )
            for item in (comparison.get("files") or [])
        ]
        return CompareOut(
            base=base,
            head=head,
            ahead_by=int(comparison.get("ahead_by") or 0),
            behind_by=int(comparison.get("behind_by") or 0),
            total_commits=int(comparison.get("total_commits") or 0),
            files=files,
        )

    # -- Customization --------------------------------------------------------

    async def get_config(
        self, repository_id: str, user: dict, branch: str = ""
    ) -> ConfigOut:
        row = await self.resolve(repository_id, user)
        ref = branch or str(row.get("default_branch") or "main")
        data = await self._raw_file(row, CONFIG_PATH, ref, required=False)
        if not data:
            config = default_config()
            return ConfigOut(
                repository_id=str(row["id"]),
                branch=ref,
                path=CONFIG_PATH,
                exists=False,
                config=config,
                yaml=dump_config(config),
            )
        raw = str(data.get("content") or "")
        text = base64.b64decode(raw).decode("utf-8", errors="replace")
        return ConfigOut(
            repository_id=str(row["id"]),
            branch=ref,
            path=CONFIG_PATH,
            exists=True,
            sha=str(data.get("sha") or ""),
            config=parse_config(text),
            yaml=text,
        )

    async def preview_config(
        self, repository_id: str, user: dict, payload: ConfigPreviewRequest
    ) -> ConfigPreviewOut:
        current = await self.get_config(repository_id, user, payload.branch)
        after = dump_config(payload.config)
        diff = config_diff(current.yaml, after)
        return ConfigPreviewOut(
            path=CONFIG_PATH,
            branch=current.branch,
            diff=diff,
            changed=bool(diff),
        )

    async def apply_config(
        self, repository_id: str, user: dict, payload: ConfigApplyRequest, request_id: str = ""
    ) -> CommitOut:
        row = await self.resolve(repository_id, user, write=True)
        branch = payload.branch or str(row.get("default_branch") or "main")
        key = payload.idempotency_key or f"file:{branch}:{CONFIG_PATH}"
        cached = await self._cached(user, key)
        if cached is not None:
            return self._commit_out(cached, CONFIG_PATH, branch)
        current = await self.get_config(repository_id, user, payload.branch)
        write = FileWriteRequest(
            path=CONFIG_PATH,
            content=dump_config(payload.config),
            message=payload.message,
            branch=current.branch,
            sha=current.sha,
            idempotency_key=payload.idempotency_key,
        )
        return await self.write_file(repository_id, user, write, request_id)

    async def templates(self, repository_id: str, user: dict) -> TemplateListOut:
        await self.resolve(repository_id, user)
        return TemplateListOut(templates=builtin_templates())

    # -- Audit + permissions --------------------------------------------------

    async def audit(
        self, repository_id: str, user: dict, limit: int = 100
    ) -> RepoAuditListOut:
        row = await self.resolve(repository_id, user)
        if not _is_admin(user):
            role = await self.repo.get_role(str(row["id"]), str(user.get("sub") or ""))
            if role not in ("owner", "write", "read"):
                raise HTTPException(status_code=403, detail="Repository access denied")
        entries = await self.repo.list_audit(str(row["id"]), limit)
        return RepoAuditListOut(entries=entries)

    async def permissions(self, repository_id: str) -> RepoRoleListOut:
        entries = await self.repo.list_permissions(repository_id)
        return RepoRoleListOut(entries=entries)

    async def grant(
        self, repository_id: str, user_id: str, role: str, actor: str
    ) -> dict:
        return await self.repo.grant_permission(repository_id, user_id, role, actor)

    async def revoke(self, repository_id: str, user_id: str) -> bool:
        return await self.repo.revoke_permission(repository_id, user_id)

    @staticmethod
    def path_segment(value: str) -> str:
        return quote(str(value), safe="")


def get_repo_ops_service() -> RepoOpsService:
    return RepoOpsService()
