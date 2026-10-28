import { api, getSessionId } from "./client";

export function placeOrder(customer, paymentMethod) {
  return api.post("/api/orders/place", {
    session_id: getSessionId(),
    customer,
    paymentMethod,
  });
}

export function getOrders() {
  return api.get(`/api/orders/${getSessionId()}`);
}

export function getOrderDetail(orderId) {
  return api.get(`/api/orders/detail/${orderId}`);
}
