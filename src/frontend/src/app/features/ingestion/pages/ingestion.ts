import { Component, inject, signal } from "@angular/core";
import { IngestionApiService } from "../services/ingestion";
import { FormControl } from "@angular/forms";
import { form, FormField } from "@angular/forms/signals";

@Component({
    selector: "app-ingestion-page",
    templateUrl: "./ingestion.html",
    styleUrl: "./ingestion.scss",
    imports: [FormField]
})
export class IngestionPage {
    private readonly service = inject(IngestionApiService);

    addRepositoryModel = signal({
        repository: ""
    });
    addRepositoryForm = form(this.addRepositoryModel);
}