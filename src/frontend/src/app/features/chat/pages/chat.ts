import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from "@angular/core";
import { form, FormField } from "@angular/forms/signals";
import { Subscription } from "rxjs";
import { ChatEvent, ChatMessage } from "../models/chat";
import { ChatApiService } from "../services/chat";

@Component({
	selector: "app-chat-page",
	templateUrl: "./chat.html",
	styleUrl: "./chat.scss",
	imports: [FormField],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChatPage {
	private readonly service = inject(ChatApiService);
	private nextId = 1;
	private subscription: Subscription | null = null;

	protected readonly messages = signal<ChatMessage[]>([]);
	protected readonly busy = signal(false);

	protected readonly questionModel = signal({
		question: ""
	});
	protected readonly questionForm = form(this.questionModel);

	constructor() {
		inject(DestroyRef).onDestroy(() => this.subscription?.unsubscribe());
	}

	protected send(event: Event): void {
		event.preventDefault();

		const question = this.questionModel().question.trim();
		if (question.length === 0 || this.busy()) {
			return;
		}

		const assistantId = this.nextId + 1;
		this.messages.update(messages => [
			...messages,
			{ id: this.nextId, role: "user", content: question, sources: [], error: null, streaming: false },
			{ id: assistantId, role: "assistant", content: "", sources: [], error: null, streaming: true }
		]);
		this.nextId += 2;
		this.questionModel.set({ question: "" });
		this.busy.set(true);

		this.subscription = this.service.ask(question).subscribe({
			next: chatEvent => this.apply(assistantId, chatEvent),
			error: () => this.finish(assistantId, "Could not reach the server. Please try again."),
			complete: () => this.finish(assistantId, null)
		});
	}

	protected stop(): void {
		this.subscription?.unsubscribe();
		this.subscription = null;
		this.messages.update(messages =>
			messages.map(message => (message.streaming ? { ...message, streaming: false } : message))
		);
		this.busy.set(false);
	}

	private apply(id: number, chatEvent: ChatEvent): void {
		switch (chatEvent.type) {
			case "sources":
				this.patch(id, message => ({ ...message, sources: chatEvent.sources }));
				break;
			case "token":
				this.patch(id, message => ({ ...message, content: message.content + chatEvent.text }));
				break;
			case "error":
				this.patch(id, message => ({ ...message, error: chatEvent.message }));
				break;
			case "done":
				break;
		}
	}

	private finish(id: number, error: string | null): void {
		this.patch(id, message => ({
			...message,
			streaming: false,
			error: message.error ?? error
		}));
		this.subscription = null;
		this.busy.set(false);
	}

	private patch(id: number, change: (message: ChatMessage) => ChatMessage): void {
		this.messages.update(messages => messages.map(message => (message.id === id ? change(message) : message)));
	}
}
