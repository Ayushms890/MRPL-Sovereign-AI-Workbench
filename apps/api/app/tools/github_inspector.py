import httpx
from app.tools.base import ToolResult

class GithubInspectorTool:
    name = "github_inspector"
    description = (
        "Inspects a public GitHub repository. Can list repository directory files, read a file content, or view recent issues. "
        "Use this tool when answering questions about a GitHub project, inspecting repository code, or analyzing open issues."
    )
    parameters = {
        "type": "object",
        "properties": {
            "owner": {"type": "string", "description": "Repository owner or organization name (e.g. 'octocat')."},
            "repo": {"type": "string", "description": "Repository name (e.g. 'Archimedes')."},
            "action": {
                "type": "string",
                "enum": ["list_files", "read_file", "list_issues"],
                "description": "Action to perform: list_files (list tree/files), read_file (read file content), list_issues (list open issues).",
            },
            "path": {"type": "string", "description": "File or folder path within repo (used for list_files or read_file).", "default": ""},
        },
        "required": ["owner", "repo", "action"],
    }

    def execute(self, arguments: dict) -> ToolResult:
        result_text = self.run(arguments)
        return ToolResult(content=result_text)

    def run(self, arguments: dict) -> str:
        owner = arguments.get("owner", "").strip()
        repo = arguments.get("repo", "").strip()
        action = arguments.get("action", "list_files")
        path = arguments.get("path", "").strip()

        if not owner or not repo:
            return "Error: owner and repo parameters are required."

        headers = {
            "User-Agent": "Archimedes-AI-OS",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            if action == "list_files":
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                res = httpx.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                items = res.json()
                if isinstance(items, list):
                    file_list = [f"- [{item.get('type', 'file')}] {item.get('path', '')}" for item in items[:30]]
                    return f"### GitHub Contents for `{owner}/{repo}` ({path or 'root'}):\n" + "\n".join(file_list)
                return f"Path `{path}` is a file. Use action 'read_file' to view its content."

            elif action == "read_file":
                if not path:
                    return "Error: path parameter is required for read_file action."
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
                res = httpx.get(raw_url, headers=headers, timeout=10)
                if res.status_code == 404:
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
                    res = httpx.get(raw_url, headers=headers, timeout=10)
                res.raise_for_status()
                content = res.text[:3000]
                truncated = "\n\n...[Content truncated]" if len(res.text) > 3000 else ""
                return f"### Contents of `{owner}/{repo}/{path}`:\n```\n{content}{truncated}\n```"

            elif action == "list_issues":
                url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=10"
                res = httpx.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                issues = res.json()
                if not issues:
                    return f"No open issues found for `{owner}/{repo}`."
                issue_list = [f"#{item.get('number')}: [{item.get('title')}]({item.get('html_url')})" for item in issues]
                return f"### Open Issues for `{owner}/{repo}`:\n" + "\n".join(issue_list)

            return f"Error: Unknown action '{action}'."

        except httpx.HTTPStatusError as exc:
            return f"Error: GitHub API returned HTTP {exc.response.status_code} — {exc.response.text[:200]}"
        except httpx.HTTPError as exc:
            return f"Error: Could not reach GitHub API ({exc})."
