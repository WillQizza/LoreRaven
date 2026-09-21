import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { InjestedRepository } from '../models/repository';

@Injectable({
  providedIn: 'root'
})
export class IngestionApiService {
  private readonly http = inject(HttpClient);

  getRepositories(): Observable<readonly InjestedRepository[]> {
    return this.http.get<readonly InjestedRepository[]>('/api/repositories');
  }

  addRepository(url: string): Observable<InjestedRepository> {
    return this.http.post<InjestedRepository>('/api/repositories', { url });
  }

  removeRepository(id: number): Observable<void> {
    return this.http.delete<void>(`/api/repositories/${id}`);
  }
}
