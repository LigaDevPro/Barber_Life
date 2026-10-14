import { Component, Input } from '@angular/core';

@Component({
  selector: 'bl-logo',
  standalone: true,
  template: `
    <img
      src="img/logo.png"
      [style.width.px]="size"
      [style.height.px]="size"
      [alt]="decorativo ? '' : 'Barber Life'"
      class="object-contain"
    />
  `,
})
export class LogoComponent {
  @Input() size = 56;
  /** Si el logo acompaña al texto "Barber Life", es decorativo (alt vacío) para no repetir el nombre. */
  @Input() decorativo = false;
}
