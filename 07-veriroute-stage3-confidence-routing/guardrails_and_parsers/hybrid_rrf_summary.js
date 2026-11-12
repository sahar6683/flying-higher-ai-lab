// Source-aligned Stage 2 scoring example for an n8n Code node (Run Once for Each Item).
// Input contract: $json.s2_top_1_jina_score is the reranked winner's Jina score;
// $json.s2_top_1_rrf_score is that same winner's Stage 1 Qdrant RRF score.
// This explicit contract avoids blending Jina's winner with the unrelated Stage 1 rank-1 score.
const jina = Number($json.s2_top_1_jina_score);
const rrf = Number($json.s2_top_1_rrf_score);
const rrfCeiling = 0.50;

if (!Number.isFinite(jina) || !Number.isFinite(rrf) || jina < 0 || jina > 1 || rrf < 0) {
  return [{json: {...$json, blended_score: null, routing_tier: "ROUTING_ERROR_FALLBACK", route_error: "INVALID_SCORE_COMPONENT"}}];
}

const normalizedRrf = Math.min(rrf / rrfCeiling, 1.0);
const blended = (0.80 * jina) + (0.20 * normalizedRrf);
let tier;
if (blended >= 0.45) tier = "Tier 1";
else if (blended >= 0.22) tier = "Tier 2";
else tier = "Tier 3";

return [{json: {...$json, normalized_rrf: normalizedRrf, blended_score: blended, routing_tier: tier}}];
