import client from './client';

export const getAdminSystem   = () => client.get('/admin/system').then(r => r.data);
export const getAdminQueues   = () => client.get('/admin/queues').then(r => r.data);
export const getAdminIngestion = () => client.get('/admin/ingestion').then(r => r.data);
export const getAdminScores   = () => client.get('/admin/scores').then(r => r.data);
export const getAdminAlertStats = () => client.get('/admin/alerts/stats').then(r => r.data);

export const getWhatsAppStatus  = () => client.get('/admin/whatsapp/status').then(r => r.data);
export const whatsAppBroadcast  = (message) =>
  client.post('/admin/whatsapp/broadcast', { message }).then(r => r.data);
