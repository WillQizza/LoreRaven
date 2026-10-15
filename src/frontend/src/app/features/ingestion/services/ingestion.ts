import { HttpClient } from "@angular/common/http";
import { inject, Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { IngestedRepository } from "../models/repository";

@Injectable({
	providedIn: "root"
})
export class IngestionApiService {
	private readonly http = inject(HttpClient);

	getRepositories(): Observable<IngestedRepository[]> {
		return this.http.get<IngestedRepository[]>("/api/repositories");
	}

	addRepository(url: string): Observable<IngestedRepository> {
		return this.http.post<IngestedRepository>("/api/repositories", { url });
	}

	removeRepository(id: number): Observable<void> {
		return this.http.delete<void>(`/api/repositories/${id}`);
	}
}
