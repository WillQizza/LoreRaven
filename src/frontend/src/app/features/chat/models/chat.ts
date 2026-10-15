export type ChatEvent =
	| { type: "sources"; sources: string[] }
	| { type: "token"; text: string }
	| { type: "done" }
	| { type: "error"; message: string };

export interface ChatMessage {
	id: number;
	role: "user" | "assistant";
	content: string;
	sources: string[];
	error: string | null;
	streaming: boolean;
}
