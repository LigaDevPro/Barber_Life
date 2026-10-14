import { AfterViewInit, Directive, ElementRef, OnDestroy, output } from '@angular/core';

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Gestión de foco para diálogos modales (WCAG 2.1.2, 2.4.3 y patrón ARIA "dialog"):
 * al abrir mueve el foco adentro, cierra con Esc, mantiene Tab/Shift+Tab dentro
 * del diálogo y al cerrar devuelve el foco al elemento que lo abrió.
 */
@Directive({
  selector: '[blDialogFocus]',
  standalone: true,
  host: { '(keydown)': 'onKeydown($event)', tabindex: '-1' },
})
export class DialogFocusDirective implements AfterViewInit, OnDestroy {
  readonly blDialogClose = output<void>();
  private anterior: HTMLElement | null = document.activeElement as HTMLElement | null;

  constructor(private readonly ref: ElementRef<HTMLElement>) {}

  ngAfterViewInit(): void {
    const el = this.ref.nativeElement;
    (el.querySelector<HTMLElement>(FOCUSABLE) ?? el).focus();
  }

  ngOnDestroy(): void {
    this.anterior?.focus?.();
  }

  onKeydown(e: KeyboardEvent): void {
    if (e.key === 'Escape') {
      e.stopPropagation();
      this.blDialogClose.emit();
      return;
    }
    if (e.key !== 'Tab') return;
    const items = Array.from(this.ref.nativeElement.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (items.length === 0) {
      e.preventDefault();
      return;
    }
    const primero = items[0];
    const ultimo = items[items.length - 1];
    const activo = document.activeElement;
    if (e.shiftKey && (activo === primero || activo === this.ref.nativeElement)) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && activo === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  }
}
