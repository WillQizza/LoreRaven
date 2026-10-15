import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { ChatEvent } from "../models/chat";

@Injectable({
	providedIn: "root"
})
export class ChatApiService {
	ask(question: string): Observable<ChatEvent> {
		return new Observable<ChatEvent>(subscriber => {
			const controller = new AbortController();

			this.stream(question, controller.signal, event => subscriber.next(event))
				.then(() => subscriber.complete())
				.catch(error => {
					if (!controller.signal.aborted) {
						subscriber.error(error);
					}
				});

			return () => controller.abort();
		});
	}

	private async stream(question: string, signal: AbortSignal, emit: (event: ChatEvent) => void): Promise<void> {
		const response = await fetch("/api/chat", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ question }),
			signal
		});

		if (!response.ok || response.body === null) {
			throw new Error(`Request failed with status ${response.status}.`);
		}

		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let buffer = "";

		while (true) {
			const { done, value } = await reader.read();
			if (done) {
				break;
			}

			buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

			let boundary = buffer.indexOf("\n\n");
			while (boundary !== -1) {
				const event = this.parseFrame(buffer.slice(0, boundary));
				buffer = buffer.slice(boundary + 2);
				if (event !== null) {
					emit(event);
				}

				boundary = buffer.indexOf("\n\n");
			}
		}
	}

	private parseFrame(frame: string): ChatEvent | null {
		let name = "message";
		const dataLines: string[] = [];

		for (const line of frame.split("\n")) {
			if (line.startsWith("event:")) {
				name = line.slice(6).trim();
			} else if (line.startsWith("data:")) {
				dataLines.push(line.slice(5).trimStart());
			}
		}

		if (dataLines.length === 0) {
			return null;
		}

		const data: unknown = JSON.parse(dataLines.join("\n"));

		switch (name) {
			case "sources":
				return {
					type: "sources",
					sources: Array.isArray(data) ? data.map(item => (item ?? "").toString()) : []
				};
			case "token":
				return { type: "token", text: (data ?? "").toString() };
			case "done":
				return { type: "done" };
			case "error":
				return { type: "error", message: (data ?? "").toString() };
			default:
				return null;
		}
	}
}
