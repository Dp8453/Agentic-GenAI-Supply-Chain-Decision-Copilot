import apiClient from './client';

export const getInventoryRisks = async (params = {}) => {
  const response = await apiClient.get('/risk', { params });
  return response.data;
};

export const getProductRiskDetail = async (productId, warehouseId = null) => {
  const params = warehouseId ? { warehouse_id: warehouseId } : {};
  const response = await apiClient.get(`/risk/${productId}`, { params });
  return response.data;
};

export const getProcurementRecommendations = async (params = {}) => {
  const response = await apiClient.get('/recommendations', { params });
  return response.data;
};
