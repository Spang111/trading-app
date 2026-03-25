const DEFAULT_BACKEND_API_URL = "https://backend-766691451715.asia-southeast1.run.app"

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "")
}

export function getBackendApiBaseUrl() {
  const configuredUrl =
    process.env.BACKEND_API_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    DEFAULT_BACKEND_API_URL

  return trimTrailingSlash(configuredUrl)
}
