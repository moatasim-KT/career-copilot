
export interface AnalyticsUpdatePayload {
  [key: string]: any;
}

export function handleAnalyticsUpdate(
  payload: AnalyticsUpdatePayload,
  setData: (data: any) => void,
) {
  setData(payload);
}
