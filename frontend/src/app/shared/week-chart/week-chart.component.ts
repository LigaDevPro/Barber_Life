import { Component, Input, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TurnoPorDia } from '../../core/models/models';

@Component({
  selector: 'bl-week-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <svg [attr.viewBox]="'0 0 320 110'" class="block h-22.5 w-full" preserveAspectRatio="none">
      <polyline
        [attr.points]="linePoints()"
        fill="none"
        stroke="var(--color-bl-accent)"
        stroke-width="2.5"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
      <polygon [attr.points]="areaPoints()" fill="url(#chart-fill)" opacity="0.35" />
      <defs>
        <linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#8b6fe0" />
          <stop offset="100%" stop-color="#8b6fe0" stop-opacity="0" />
        </linearGradient>
      </defs>
      @for (p of points(); track $index) {
        <circle [attr.cx]="p.x" [attr.cy]="p.y" r="2.5" fill="var(--color-bl-accent)" />
      }
    </svg>
    <div class="mt-1 flex justify-between text-[11px] text-bl-text-muted">
      @for (d of diasValue(); track d.dia) {
        <span>{{ d.dia }}</span>
      }
    </div>
  `,
  host: { class: 'block' },
})
export class WeekChartComponent {
  private _dias = signal<TurnoPorDia[]>([]);
  @Input() set dias(value: TurnoPorDia[]) {
    this._dias.set(value || []);
  }
  diasValue = () => this._dias();

  points = computed(() => {
    const data = this._dias();
    if (!data.length) return [];
    const max = Math.max(1, ...data.map((d) => d.cantidad));
    const stepX = 320 / (data.length - 1 || 1);
    return data.map((d, i) => ({
      x: i * stepX,
      y: 100 - (d.cantidad / max) * 90,
    }));
  });

  linePoints = computed(() =>
    this.points()
      .map((p) => `${p.x},${p.y}`)
      .join(' '),
  );

  areaPoints = computed(() => {
    const pts = this.points();
    if (!pts.length) return '';
    return `0,100 ${this.linePoints()} 320,100`;
  });
}
