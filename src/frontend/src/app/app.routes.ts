import { Routes } from '@angular/router';
import { ChatPage } from './features/chat/pages/chat';
import { IngestionPage } from './features/ingestion/pages/ingestion';
import { NotFoundPage } from './features/not-found/pages/not-found';

export const routes: Routes = [
    {
        path: "chat",
        component: ChatPage
    },
    {
        path: "ingest",
        component: IngestionPage
    },
    {
        path: "",
        pathMatch: "full",
        redirectTo: "chat"
    },
    {
        path: "**",
        component: NotFoundPage
    }
];
