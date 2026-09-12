import apiClient from './client';

export const getDemandForecast = async (productId, horizonDays = 14) => {
  const response = await apiClient.post('/forecast', {
    product_id: productId,
    horizon_days: horizonDays,
  });
  return response.data;
};
