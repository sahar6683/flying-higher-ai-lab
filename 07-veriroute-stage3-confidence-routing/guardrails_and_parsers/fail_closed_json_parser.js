// n8n Code-node helper: fail-closed verifier parser. Call with the HTTP node output.
function parseVerifierFailClosed(response) {
  if (!response || response.error) {
    return { passed: false, reason: "VERIFIER_HTTP_ERROR_FAIL_CLOSED", details: String(response?.error?.message || response?.error || "empty response").slice(0, 160) };
  }
  try {
    const raw = response?.choices?.[0]?.message?.content;
    if (typeof raw !== "string" || !raw.trim()) throw new Error("missing content");
    const clean = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();
    const parsed = JSON.parse(clean);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("expected object");
    const passed = parsed.verification_passed === true; // strict boolean only
    const noViolation = !parsed.violation_type || parsed.violation_type === "NONE";
    return { passed: passed && noViolation, reason: passed && noViolation ? "VERIFIED" : (parsed.violation_type || parsed.failure_reason || "VERIFIER_REJECTED"), auditor_notes: String(parsed.auditor_explanation || parsed.auditor_notes || ""), telemetry: { parse_ok: true, verifier_http_error: false } };
  } catch (error) {
    return { passed: false, reason: "VERIFIER_MALFORMED_JSON_FAIL_CLOSED", details: String(error.message || error).slice(0, 160), telemetry: { parse_ok: false, verifier_http_error: false } };
  }
}
return [{ json: { ...$json, verifier_result: parseVerifierFailClosed($json) } }];
