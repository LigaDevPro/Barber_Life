import { Component } from '@angular/core';
import { LogoComponent } from '../logo/logo.component';

/** Panel de marca de login/registro en escritorio (Figma: "01_Login (desktop)"). */
@Component({
  selector: 'bl-auth-hero',
  standalone: true,
  imports: [LogoComponent],
  template: `
    <section class="bl-hero-gradient flex h-full flex-col justify-center px-24 py-16 text-bl-text">
      <bl-logo [size]="96" />
      <h2 class="mt-8 mb-6 max-w-lg text-[56px] leading-[1.1] font-extrabold">Tu turno, sin vueltas.</h2>
      <p class="mb-8 max-w-lg text-[17px] leading-relaxed text-bl-text/80">
        Conocé lo que ofrecemos, elegí con quién atenderte y solicitá tu turno online en pocos minutos.
      </p>
      <ul class="m-0 flex list-none flex-col gap-4 p-0 text-[16px]">
        @for (item of beneficios; track item) {
          <li class="flex items-center gap-3">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="m5 12.5 4.5 4.5L19 7.5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            {{ item }}
          </li>
        }
      </ul>
    </section>
  `,
})
export class AuthHeroComponent {
  beneficios = ['Solicitá tu turno online', 'Elegí con quién atenderte', 'Pagá con Mercado Pago'];
}
