export type Status = 'new' | 'awaiting_review' | 'in_progress' | 'completed'
export const statusLabels: Record<Status, string> = { new: 'New', awaiting_review: 'Awaiting review', in_progress: 'In progress', completed: 'Completed' }
export type RequestItem = { id: string; title: string; description: string; creator_handle: string; created_at: string; updated_at: string; status: Status }
export type Task = { id: string; request_id: string; title: string; rationale: string; priority: 'low' | 'medium' | 'high'; state: 'open' | 'done'; updated_at: string }
export type Detail = RequestItem & { tasks: Task[] }
export type Page = { items: RequestItem[]; total: number; limit: number; offset: number }
export type Dashboard = { total_requests: number; requests_by_status: Record<Status, number>; total_tasks: number; open_tasks: number; completed_tasks: number; recent_requests: RequestItem[]; recent_tasks: Task[] }
