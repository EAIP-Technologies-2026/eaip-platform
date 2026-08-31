"""SdkGenerator — multi-language client code generation."""

from __future__ import annotations

import re
from typing import Any

from eaip.logging.context import get_logger
from eaip.sdk.exceptions import GenerationError, LanguageNotSupportedError
from eaip.sdk.models import SdkConfig, SdkDefinition, SdkEndpoint

_SUPPORTED: set[str] = {"python", "javascript", "java", "go", "dotnet"}

_PYTHON_TEMPLATES: dict[str, str] = {
    "client_header": """from __future__ import annotations

import httpx
from typing import Any


class {name}Client:
    \"\"\"Auto-generated client for {description}\"\"\"

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        headers = {{"Authorization": f"Bearer {{api_key}}"}} if api_key else {{}}
        self._client = httpx.Client(base_url=self._base_url, headers=headers)
""",
    "endpoint_method": """
    def {method_name}(self{params}) -> dict[str, Any]:
        \"\"\"{description}\"\"\"
        response = self._client.{http_method}("{path}"{body})
        response.raise_for_status()
        return response.json()
""",
}

_JAVASCRIPT_TEMPLATES: dict[str, str] = {
    "client_header": """/**
 * Auto-generated client for {description}
 */

class {name}Client {{
  private baseUrl: string;
  private apiKey: string | undefined;

  constructor(baseUrl: string, apiKey?: string) {{
    this.baseUrl = baseUrl.replace(/\\/+$/, "");
    this.apiKey = apiKey;
  }}
""",
    "endpoint_method": """
  async {method_name}({params}): Promise<any> {{
    const url = `${{this.baseUrl}}{path}`;
    const headers: Record<string, string> = {{}};
    if (this.apiKey) headers["Authorization"] = `Bearer ${{this.apiKey}}`;
    const options: RequestInit = {{ method: "{method_verb}", headers }};
    {body_field}
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  }}
""",
}

_JAVA_TEMPLATES: dict[str, str] = {
    "client_header": """package {package};

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class {name}Client {{
    private final String baseUrl;
    private final String apiKey;
    private final HttpClient httpClient;

    public {name}Client(String baseUrl, String apiKey) {{
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.apiKey = apiKey;
        this.httpClient = HttpClient.newHttpClient();
    }}
""",
    "endpoint_method": """
    public String {methodName}({params}) throws Exception {{
        var request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "{path}"))
            .header("Authorization", "Bearer " + apiKey)
            .method("{method_verb}", {body_field})
            .build();
        var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() >= 400) throw new RuntimeException(response.body());
        return response.body();
    }}
""",
}

_GO_TEMPLATES: dict[str, str] = {
    "client_header": """package {package}

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type {name}Client struct {{
	baseURL string
	apiKey  string
	client  *http.Client
}}

func New{name}Client(baseURL, apiKey string) *{name}Client {{
	return &{name}Client{{
		baseURL: baseURL,
		apiKey:  apiKey,
		client:  &http.Client{{}},
	}}
}}
""",
    "endpoint_method": """
func (c *{name}Client) {methodName}({params}) ({returnType}, error) {{
	req, err := http.NewRequest("{httpMethod}", c.baseURL+"{path}", nil)
	if err != nil {{
		return nil, fmt.Errorf("request creation failed: %w", err)
	}}
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	resp, err := c.client.Do(req)
	if err != nil {{
		return nil, fmt.Errorf("request failed: %w", err)
	}}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {{
		return nil, fmt.Errorf("read failed: %w", err)
	}}
	if resp.StatusCode >= 400 {{
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}}
	return body, nil
}}
""",
}

_DOTNET_TEMPLATES: dict[str, str] = {
    "client_header": """using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace {package}
{{
    public class {name}Client
    {{
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;

        public {name}Client(string baseUrl, string apiKey)
        {{
            _baseUrl = baseUrl.TrimEnd('/');
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Bearer", apiKey);
        }}
""",
    "endpoint_method": """
        public async Task<string> {methodName}({params})
        {{
            var response = await _httpClient.{httpMethod}Async(_baseUrl + "{path}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsStringAsync();
        }}
""",
}


def _to_snake(name: str) -> str:
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def _to_pascal(name: str) -> str:
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    words = s2.replace("-", "_").replace(".", "_").split("_")
    return "".join(w if w.isupper() else w.capitalize() for w in words)


def _to_camel(name: str) -> str:
    pascal = _to_pascal(name)
    return pascal[0].lower() + pascal[1:]


def _template_bag(language: str) -> dict[str, str]:
    if language == "python":
        return _PYTHON_TEMPLATES
    if language == "javascript":
        return _JAVASCRIPT_TEMPLATES
    if language == "java":
        return _JAVA_TEMPLATES
    if language == "go":
        return _GO_TEMPLATES
    if language == "dotnet":
        return _DOTNET_TEMPLATES
    raise LanguageNotSupportedError(
        f"Language {language!r} is not supported",
        context={"language": language},
    )


class SdkGenerator:
    """Generates client SDK code in multiple languages."""

    def __init__(self, config: SdkConfig | None = None) -> None:
        self._config = config or SdkConfig()
        self._log = get_logger("eaip.sdk.generator")

    async def generate_client(
        self,
        sdk: SdkDefinition,
        language: str,
        endpoints: list[SdkEndpoint] | None = None,
        _config: dict[str, Any] | None = None,
    ) -> str:
        if language not in _SUPPORTED:
            raise LanguageNotSupportedError(
                f"Language {language!r} is not supported",
                context={"language": language, "supported": list(_SUPPORTED)},
            )
        if language not in self._config.supported_languages:
            raise LanguageNotSupportedError(
                f"Language {language!r} is not enabled in config",
                context={"language": language, "enabled": list(self._config.supported_languages)},
            )

        try:
            templates = _template_bag(language)
            parts: list[str] = []

            header = templates["client_header"].format(
                name=_to_pascal(sdk.name),
                description=sdk.description or sdk.name,
                package=_to_snake(sdk.name).replace("-", "_"),
            )
            parts.append(header)

            if endpoints:
                for ep in endpoints:
                    method_code = self.generate_endpoint_code(ep, language, sdk_name=sdk.name)
                    parts.append(method_code)

            if language == "python":
                parts.append("\n\n    def close(self) -> None:\n        self._client.close()\n")
            elif language in ("javascript", "java", "go", "dotnet"):
                pass

            closing = {
                "python": "",
                "javascript": "\n}}\n",
                "java": "\n}}\n",
                "go": "\n}}\n",
                "dotnet": "\n    }}\n}}\n",
            }
            parts.append(closing.get(language, ""))

            result = "".join(parts)
            if language == "go":
                result = f"package {_to_snake(sdk.name).replace('-', '_')}\n\nimport (...)" + result

            return result
        except LanguageNotSupportedError:
            raise
        except Exception as exc:
            raise GenerationError(
                f"Failed to generate {language} client: {exc}",
                context={"sdk_id": sdk.id, "language": language},
            ) from exc

    def generate_endpoint_code(
        self,
        endpoint: SdkEndpoint,
        language: str,
        sdk_name: str = "",
    ) -> str:
        templates = _template_bag(language)
        template = templates["endpoint_method"]

        raw_method_name = endpoint.id.replace("-", "_") if endpoint.id else "endpoint"
        method_name = (
            _to_snake(raw_method_name) if language == "python" else _to_camel(raw_method_name)
        )
        http_method = endpoint.method.lower()
        params_str = ""
        body_field = ""
        return_type = "dict[str, Any]"

        if language == "python":
            has_body = http_method in ("post", "put", "patch")
            params_str = ", **kwargs" if has_body else ", params: dict[str, Any] | None = None"
            body = ", json=kwargs" if has_body else ", params=params"
            body_field = body if body else ""
        elif language == "javascript":
            params_str = "params = {}"
            has_body = http_method in ("post", "put", "patch")
            body_field = "options.body = JSON.stringify(params);" if has_body else ""
        elif language == "java":
            has_body = http_method in ("post", "put", "patch")
            params_str = "String requestBody" if has_body else ""
            body_field = (
                "HttpRequest.BodyPublishers.ofString(requestBody)"
                if has_body
                else "HttpRequest.BodyPublishers.noBody()"
            )
        elif language == "go":
            params_str = ""
            return_type = "[]byte"
        elif language == "dotnet":
            params_str = ""
            http_method = http_method.capitalize()

        method_verb = http_method.upper()
        pascal_name = _to_pascal(sdk_name) if sdk_name else "Sdk"

        if language in ("java", "go"):
            http_method_literal = method_verb
        elif language == "dotnet":
            http_method_literal = http_method.capitalize()
        else:
            http_method_literal = http_method

        return template.format(
            method_name=method_name,
            methodName=method_name,
            params=params_str,
            description=endpoint.description or endpoint.path,
            path=endpoint.path,
            http_method=http_method,
            httpMethod=http_method_literal,
            returnType=return_type,
            package=_to_snake(sdk_name).replace("-", "_") if sdk_name else "sdk",
            body=body_field,
            body_field=body_field,
            return_type=return_type,
            name=pascal_name,
            method_verb=method_verb,
        )

    def generate_model_code(self, model: Any, language: str) -> str:
        if language == "python":
            fields = ""
            if hasattr(model, "fields"):
                fields = "\n".join(f"    {k}: {v}" for k, v in model.fields.items())
            model_name = _to_pascal(model.name) if hasattr(model, "name") else "Model"
            return f"\n\nclass {model_name}(BaseModel):\n{fields}\n"
        if language in ("javascript", "java", "go", "dotnet"):
            return f"\n// Model: {getattr(model, 'name', 'Model')}\n"
        return ""

    def generate_config_code(self, config: dict[str, Any] | SdkConfig, language: str) -> str:
        _template_bag(language)
        if language == "python":
            items = (
                "\n".join(f'    "{k}": {v!r},' for k, v in config.items())
                if isinstance(config, dict)
                else ""
            )
            return f"\n\nSDK_CONFIG: dict[str, Any] = {{\n{items}\n}}\n"
        return "\n// SDK configuration\n"
