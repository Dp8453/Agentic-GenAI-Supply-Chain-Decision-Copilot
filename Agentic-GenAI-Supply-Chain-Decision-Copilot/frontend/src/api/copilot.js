import apiClient from './client';

export const runAgentQuery = async ({ question, supplierFilter = null, topK = 5, providerOverride = null }) => {
  const response = await apiClient.post('/agent/query', {
    question,
    supplier_filter: supplierFilter,
    top_k: topK,
    provider_override: providerOverride,
  });
  return response.data;
};

export const getAgentGraph = async () => {
  const response = await apiClient.get('/agent/graph');
  return response.data;
};
