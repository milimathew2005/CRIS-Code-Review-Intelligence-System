from pydantic import BaseModel, Field
from typing import Optional

class WebhookUser(BaseModel):
    """
    Pydantic schema representing the GitHub user who initiated actions.
    """
    login: str = Field(..., description="The user's GitHub username handle.")

class WebhookPullRequestHead(BaseModel):
    """
    Pydantic schema representing the head commit of a pull request.
    """
    sha: str = Field(..., description="The SHA commit hash of the head branch.")

class WebhookPullRequest(BaseModel):
    """
    Pydantic schema representing the pull request metadata properties.
    """
    number: int = Field(..., description="Pull request numeric identifier.")
    title: str = Field(..., description="The subject title of the pull request.")
    user: WebhookUser = Field(..., description="The author of the pull request.")
    html_url: str = Field(..., description="The browser link referencing this pull request.")
    head: Optional[WebhookPullRequestHead] = Field(None, description="The head branch information including commit SHA.")


class WebhookRepositoryOwner(BaseModel):
    """
    Pydantic schema representing the repository owner details.
    """
    login: str = Field(..., description="Owner's GitHub handle/login.")

class WebhookRepository(BaseModel):
    """
    Pydantic schema representing the repository payload details.
    """
    name: str = Field(..., description="The name of the target repository.")
    owner: WebhookRepositoryOwner = Field(..., description="Details of the repository owner.")

class GitHubPullRequestWebhook(BaseModel):
    """
    Core schema validating the pull_request event payload subset from GitHub webhooks.
    """
    action: str = Field(..., description="The pull request lifecycle action status (e.g. opened, synchronize, reopened).")
    number: int = Field(..., description="Pull request identification number.")
    pull_request: WebhookPullRequest = Field(..., description="The specific pull request details.")
    repository: WebhookRepository = Field(..., description="The repository target metadata.")
