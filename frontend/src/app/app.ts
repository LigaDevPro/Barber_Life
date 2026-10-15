import { DOCUMENT } from '@angular/common';
import { Component, Injector, afterNextRender, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html',
  host: { class: 'block' },
})
export class App {
  private readonly router = inject(Router);
  private readonly injector = inject(Injector);
  private readonly document = inject(DOCUMENT);
  private primeraCarga = true;

  constructor() {
    // WCAG 2.4.3: en una SPA el navegador no mueve el foco al cambiar de vista,
    // así que el lector de pantalla no se entera. Lo llevamos al <h1> de la nueva vista.
    this.router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        if (this.primeraCarga) {
          this.primeraCarga = false;
          return;
        }
        afterNextRender(() => this.enfocarTitulo(), { injector: this.injector });
      });
  }

  private enfocarTitulo(): void {
    const destino = this.document.querySelector<HTMLElement>('h1') ?? this.document.querySelector<HTMLElement>('main');
    if (!destino) return;
    destino.setAttribute('tabindex', '-1');
    destino.focus({ preventScroll: true });
  }
}
