
export interface ApplicationStatusUpdatePayload {
  applicationId: string;
  status: string;
}

export function handleApplicationStatusUpdate(
  payload: ApplicationStatusUpdatePayload,
  setData: (data: any) => void,
) {
  setData(payload);
}
