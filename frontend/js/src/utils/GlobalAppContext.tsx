import { createContext } from "react";
import APIService from "./APIService";
import RecordingFeedbackManager from "./RecordingFeedbackManager";
import { FlairEnum, FlairName, Flair } from "./constants";

export type GlobalAppContextT = {
  APIService: APIService;
  websocketsUrl: string;
  currentUser: ListenBrainzUser;
  spotifyAuth?: SpotifyUser;
  youtubeAuth?: YoutubeUser;
  soundcloudAuth?: SoundCloudUser;
  funkwhaleAuth?: FunkwhaleUser;
  navidromeAuth?: NavidromeUser;
  critiquebrainzAuth?: MetaBrainzProjectUser;
  appleAuth?: AppleMusicUser;
  tidalAuth?: UserToken;
  youtubeMusicAuth?: UserToken;
  musicbrainzAuth?: MetaBrainzProjectUser & {
    refreshMBToken: () => Promise<string | undefined>;
  };
  userPreferences?: UserPreferences;
  musicbrainzGenres?: string[];
  recordingFeedbackManager: RecordingFeedbackManager;
  flair?: Flair;
};
const apiService = new APIService(`${window.location.origin}/1`);

export const defaultGlobalContext: GlobalAppContextT = {
  APIService: apiService,
  websocketsUrl: "",
  currentUser: {} as ListenBrainzUser,
  spotifyAuth: {},
  youtubeAuth: {},
  soundcloudAuth: {},
  funkwhaleAuth: undefined,
  navidromeAuth: undefined,
  appleAuth: {},
  critiquebrainzAuth: {},
  tidalAuth: undefined,
  youtubeMusicAuth: undefined,
  musicbrainzAuth: {
    refreshMBToken: async () => {
      return undefined;
    },
  },
  userPreferences: {},
  musicbrainzGenres: [],
  recordingFeedbackManager: new RecordingFeedbackManager(apiService),
  flair: FlairEnum.None,
};

const GlobalAppContext = createContext<GlobalAppContextT>(defaultGlobalContext);

export default GlobalAppContext;
