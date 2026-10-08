import * as aiLive from "./ai.service";
import * as authLive from "./auth.service";
import * as chatLive from "./chat.service";
import * as conversationsLive from "./conversations.service";
import * as brandLive from "./brand.service";
import * as campaignsLive from "./campaigns.service";
import * as agentRunsLive from "./agentRuns.service";
import * as knowledgeLive from "./knowledge.service";
import * as analyticsLive from "./analytics.service";
import * as calendarLive from "./calendar.service";
import * as integrationsLive from "./integrations.service";

import * as authMock from "../mocks/auth.mock";
import * as chatMock from "../mocks/chat.mock";
import * as conversationsMock from "../mocks/conversations.mock";
import * as brandMock from "../mocks/brand.mock";
import * as campaignsMock from "../mocks/campaigns.mock";
import * as agentRunsMock from "../mocks/agentRuns.mock";
import * as knowledgeMock from "../mocks/knowledge.mock";
import * as analyticsMock from "../mocks/analytics.mock";
import * as calendarMock from "../mocks/calendar.mock";
import * as integrationsMock from "../mocks/integrations.mock";

const useMockApi = String(import.meta.env.VITE_USE_MOCK_API ?? "true").toLowerCase() !== "false";

export const isMockApiEnabled = useMockApi;

export const authService = useMockApi ? authMock : authLive;
export const chatService = useMockApi ? chatMock : chatLive;
export const conversationsService = useMockApi ? conversationsMock : conversationsLive;
export const brandService = useMockApi ? brandMock : brandLive;
export const campaignsService = useMockApi ? campaignsMock : campaignsLive;
export const agentRunsService = useMockApi ? agentRunsMock : agentRunsLive;
export const knowledgeService = useMockApi ? knowledgeMock : knowledgeLive;
export const analyticsService = useMockApi ? analyticsMock : analyticsLive;
export const calendarService = useMockApi ? calendarMock : calendarLive;
export const integrationsService = useMockApi ? integrationsMock : integrationsLive;
export const aiService = aiLive;