import { Routes } from '@angular/router';
import { ChatPage } from './features/chat/pages/chat-page';
import { InjestionPage } from './features/ingestion/pages/injestion-page';

export const routes: Routes = [
    {
        path: "chat",
        component: ChatPage
    },
    {
        path: "ingest",
        component: InjestionPage
    }
];
