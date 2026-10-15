import { HttpErrorResponse } from "@angular/common/http";
import { ChangeDetectionStrategy, Component, computed, inject, signal } from "@angular/core";
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";
import { form, FormField } from "@angular/forms/signals";
import { interval } from "rxjs";
import { IngestedRepository } from "../models/repository";
import { IngestionApiService } from "../services/ingestion";

const POLL_INTERVAL_MS = 3000;

@Component({
	selector: "app-ingestion-page",
	templateUrl: "./ingestion.html",
	styleUrl: "./ingestion.scss",
	imports: [FormField],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class IngestionPage {
	private readonly service = inject(IngestionApiService);

	protected readonly repositories = signal<IngestedRepository[]>([]);
	protected readonly loading = signal(true);
	protected readonly submitting = signal(false);
	protected readonly errorMessage = signal<string | null>(null);

	protected readonly addRepositoryModel = signal({
		repository: ""
	});
	protected readonly addRepositoryForm = form(this.addRepositoryModel);

	private readonly hasIngesting = computed(() =>
		this.repositories().some(repository => repository.status === "ingesting")
	);

	constructor() {
		this.refresh();

		interval(POLL_INTERVAL_MS)
			.pipe(takeUntilDestroyed())
			.subscribe(() => {
				if (this.hasIngesting()) {
					this.refresh();
				}
			});
	}

	protected add(event: Event): void {
		event.preventDefault();

		const url = this.addRepositoryModel().repository.trim();
		if (url.length === 0 || this.submitting()) {
			return;
		}

		this.submitting.set(true);
		this.errorMessage.set(null);
		this.service.addRepository(url).subscribe({
			next: () => {
				this.submitting.set(false);
				this.addRepositoryModel.set({ repository: "" });
				this.refresh();
			},
			error: error => {
				this.submitting.set(false);
				this.errorMessage.set(this.describe(error));
			}
		});
	}

	protected remove(repository: IngestedRepository): void {
		this.errorMessage.set(null);
		this.service.removeRepository(repository.id).subscribe({
			next: () => this.refresh(),
			error: error => this.errorMessage.set(this.describe(error))
		});
	}

	private refresh(): void {
		this.service.getRepositories().subscribe({
			next: repositories => {
				this.repositories.set(repositories);
				this.loading.set(false);
			},
			error: error => {
				this.loading.set(false);
				this.errorMessage.set(this.describe(error));
			}
		});
	}

	private describe(error: unknown): string {
		if (error instanceof HttpErrorResponse) {
			const detail: unknown = error.error?.detail;
			if (typeof detail === "string") {
				return detail;
			}
			if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
				return detail[0].msg;
			}
		}

		return "Something went wrong. Please try again.";
	}
}
