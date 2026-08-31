"""Git integration service — repository registration, commit indexing, webhook dispatch."""

from __future__ import annotations

from eaip.gitsvc.exceptions import RepositoryNotFoundError
from eaip.gitsvc.models import GitCommit, GitConfig, GitRepository, GitRepositoryStatus


class GitIntegrationService:
    def __init__(self, config: GitConfig | None = None) -> None:
        self._config = config or GitConfig()
        self._repositories: dict[str, GitRepository] = {}
        self._commits: dict[str, GitCommit] = {}

    @property
    def config(self) -> GitConfig:
        return self._config

    async def register_repository(self, repo: GitRepository) -> GitRepository:
        self._repositories[repo.id] = repo
        return repo

    async def get_repository(self, repo_id: str) -> GitRepository:
        repo = self._repositories.get(repo_id)
        if repo is None:
            raise RepositoryNotFoundError(f"Repository {repo_id} not found")
        return repo

    async def index_commit(self, commit: GitCommit) -> GitCommit:
        self._commits[commit.id] = commit
        return commit

    async def list_repositories(self) -> list[GitRepository]:
        return list(self._repositories.values())

    async def update_repository_status(
        self, repo_id: str, status: GitRepositoryStatus
    ) -> GitRepository:
        repo = await self.get_repository(repo_id)
        updated = repo.model_copy(update={"status": status, "updated_at": repo.updated_at})
        self._repositories[repo_id] = updated
        return updated


__all__ = ["GitIntegrationService"]
