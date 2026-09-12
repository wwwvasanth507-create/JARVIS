export interface InputState {
  forward: boolean;
  backward: boolean;
  left: boolean;
  right: boolean;
  jump: boolean;
  sprint: boolean;
  crouch: boolean;
  mouseX: number;
  mouseY: number;
  mouseDeltaX: number;
  mouseDeltaY: number;
  mouseWheel: number;
  isPointerLocked: boolean;
  isMouseDown: boolean;
}

export class InputManager {
  private static instance: InputManager;
  private state: InputState = {
    forward: false,
    backward: false,
    left: false,
    right: false,
    jump: false,
    sprint: false,
    crouch: false,
    mouseX: 0,
    mouseY: 0,
    mouseDeltaX: 0,
    mouseDeltaY: 0,
    mouseWheel: 0,
    isPointerLocked: false,
    isMouseDown: false,
  };

  private keysDown: Set<string> = new Set();
  private justPressed: Set<string> = new Set();
  private element: HTMLElement | null = null;
  private boundHandlers: { [key: string]: (e: any) => void } = {};

  private constructor() {
    this.bindEvents();
  }

  public static getInstance(): InputManager {
    if (!InputManager.instance) {
      InputManager.instance = new InputManager();
    }
    return InputManager.instance;
  }

  public attachToElement(el: HTMLElement): void {
    this.element = el;
  }

  public requestPointerLock(): void {
    if (this.element && document.pointerLockElement !== this.element) {
      this.element.requestPointerLock?.();
    }
  }

  public exitPointerLock(): void {
    if (document.pointerLockElement) {
      document.exitPointerLock?.();
    }
  }

  private bindEvents(): void {
    this.boundHandlers.keydown = (e: KeyboardEvent) => {
      if (!this.keysDown.has(e.code)) {
        this.justPressed.add(e.code);
      }
      this.keysDown.add(e.code);
      this.updateState();
    };

    this.boundHandlers.keyup = (e: KeyboardEvent) => {
      this.keysDown.delete(e.code);
      this.updateState();
    };

    this.boundHandlers.mousemove = (e: MouseEvent) => {
      if (this.state.isPointerLocked) {
        this.state.mouseDeltaX += e.movementX;
        this.state.mouseDeltaY += e.movementY;
      }
      this.state.mouseX = e.clientX;
      this.state.mouseY = e.clientY;
    };

    this.boundHandlers.mousedown = (e: MouseEvent) => {
      if (e.button === 0) this.state.isMouseDown = true;
    };

    this.boundHandlers.mouseup = (e: MouseEvent) => {
      if (e.button === 0) this.state.isMouseDown = false;
    };

    this.boundHandlers.wheel = (e: WheelEvent) => {
      this.state.mouseWheel = Math.sign(e.deltaY);
    };

    this.boundHandlers.pointerlockchange = () => {
      this.state.isPointerLocked = document.pointerLockElement === this.element;
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', this.boundHandlers.keydown);
      window.addEventListener('keyup', this.boundHandlers.keyup);
      window.addEventListener('mousemove', this.boundHandlers.mousemove);
      window.addEventListener('mousedown', this.boundHandlers.mousedown);
      window.addEventListener('mouseup', this.boundHandlers.mouseup);
      window.addEventListener('wheel', this.boundHandlers.wheel, { passive: true });
    }
    if (typeof document !== 'undefined') {
      document.addEventListener('pointerlockchange', this.boundHandlers.pointerlockchange);
    }
  }

  private updateState(): void {
    this.state.forward = this.keysDown.has('KeyW') || this.keysDown.has('ArrowUp');
    this.state.backward = this.keysDown.has('KeyS') || this.keysDown.has('ArrowDown');
    this.state.left = this.keysDown.has('KeyA') || this.keysDown.has('ArrowLeft');
    this.state.right = this.keysDown.has('KeyD') || this.keysDown.has('ArrowRight');
    this.state.jump = this.keysDown.has('Space');
    this.state.sprint = this.keysDown.has('ShiftLeft') || this.keysDown.has('ShiftRight');
    this.state.crouch = this.keysDown.has('ControlLeft') || this.keysDown.has('ControlRight') || this.keysDown.has('KeyC');
  }

  public isKeyJustPressed(code: string): boolean {
    return this.justPressed.has(code);
  }

  public getState(): Readonly<InputState> {
    return this.state;
  }

  public endFrame(): void {
    this.state.mouseDeltaX = 0;
    this.state.mouseDeltaY = 0;
    this.state.mouseWheel = 0;
    this.justPressed.clear();
  }

  public dispose(): void {
    window.removeEventListener('keydown', this.boundHandlers.keydown);
    window.removeEventListener('keyup', this.boundHandlers.keyup);
    window.removeEventListener('mousemove', this.boundHandlers.mousemove);
    window.removeEventListener('mousedown', this.boundHandlers.mousedown);
    window.removeEventListener('mouseup', this.boundHandlers.mouseup);
    window.removeEventListener('wheel', this.boundHandlers.wheel);
    document.removeEventListener('pointerlockchange', this.boundHandlers.pointerlockchange);
    this.keysDown.clear();
    this.justPressed.clear();
  }
}

export const input = InputManager.getInstance();
