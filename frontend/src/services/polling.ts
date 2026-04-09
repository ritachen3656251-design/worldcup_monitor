import { api } from './api';
import type { HotCard } from '../types';

type PollCallback = (newCards: HotCard[]) => void;

class PollingService {
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private lastCheck: string;
  private category: string = '全部';
  private intervalMs: number;
  private callback: PollCallback | null = null;

  constructor(intervalSeconds: number = 30) {
    this.intervalMs = intervalSeconds * 1000;
    this.lastCheck = new Date().toISOString();
  }

  start(callback: PollCallback, category: string = '全部') {
    this.callback = callback;
    this.category = category;
    this.lastCheck = new Date().toISOString();

    // Stop existing interval if any
    this.stop();

    this.intervalId = setInterval(async () => {
      await this.poll();
    }, this.intervalMs);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  setCategory(category: string) {
    this.category = category;
  }

  private async poll() {
    try {
      const response = await api.getNewCards(this.lastCheck, this.category);
      if (response.success && response.data.cards.length > 0) {
        this.lastCheck = new Date().toISOString();
        if (this.callback) {
          this.callback(response.data.cards);
        }
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }
}

export const pollingService = new PollingService(30);
export default pollingService;
