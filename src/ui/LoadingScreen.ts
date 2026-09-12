export class LoadingScreen {
  private element: HTMLElement | null = null;
  private progressFill: HTMLElement | null = null;
  private statusText: HTMLElement | null = null;

  constructor() {
    this.element = document.getElementById('loading-screen');
    this.progressFill = document.getElementById('loading-bar-fill');
    this.statusText = document.getElementById('loading-status-text');
  }

  public setProgress(percent: number, status: string): void {
    if (this.progressFill) {
      this.progressFill.style.width = `${Math.min(100, Math.max(0, percent))}%`;
    }
    if (this.statusText) {
      this.statusText.textContent = status;
    }
  }

  public hide(delayMs: number = 250): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        if (this.element) {
          this.element.classList.add('fade-out');
          setTimeout(() => {
            if (this.element) {
              this.element.style.display = 'none';
            }
            resolve();
          }, 400);
        } else {
          resolve();
        }
      }, delayMs);
    });
  }
}
