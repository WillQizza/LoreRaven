export type RepositoryStatus = "ingesting" | "ready" | "failed";

export interface IngestedRepository {
	id: number;
	url: string;
	status: RepositoryStatus;
	error: string | null;
}
