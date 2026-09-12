import apiClient from './client';

export const runNaturalLanguageSimulation = async ({ question, providerOverride = null }) => {
  const response = await apiClient.post('/simulation/query', {
    question,
    provider_override: providerOverride,
  });
  return response.data;
};

export const runStructuredSimulation = async ({ scenario, providerOverride = null }) => {
  const response = await apiClient.post('/simulation/run', scenario, {
    params: { provider_override: providerOverride },
  });
  return response.data;
};
