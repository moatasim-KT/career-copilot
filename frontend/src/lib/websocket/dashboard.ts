
export interface DashboardUpdatePayload {
  [key: string]: any;
}

export function handleDashboardUpdate(payload: DashboardUpdatePayload, setData: (data: any) => void) {
  setData(payload);
}
