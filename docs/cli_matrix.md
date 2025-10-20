# CLI Output Matrix

This matrix shows how the CLI's layout flags combine to produce files and ASCII grids.
Each preview mirrors the layout comments written into the generated SCAD files. When you
omit `--calendar-days-per-row`, the daily calendars adopt the same width as the monthly grid,
so the compact and narrow layouts relocate their `monthly-{width}x6` directories automatically.

<table>
  <thead>
    <tr>
      <th>Scenario</th>
      <th>Flags</th>
      <th>Generated files</th>
      <th>Monthly grid preview</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Single-color shelf</strong></td>
      <td>
        <code>--colors 1</code><br>
        <code>--months-per-row 12</code>
      </td>
      <td>
        <code>contributions.scad</code><br>
        Optional <code>contributions.stl</code><br>
        Yearly <code>stl/&lt;year&gt;/README.md</code><br>
        Copied <code>baseplate_2x6.scad</code>
      </td>
      <td>
        <pre>Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec</pre>
      </td>
    </tr>
    <tr>
      <td><strong>Two-tone palette</strong></td>
      <td>
        <code>--colors 2</code><br>
        <code>--months-per-row 12</code>
      </td>
      <td>
        <code>contributions_color1.scad</code><br>
        <code>contributions_color2.scad</code><br>
        Optional matching STLs<br>
        <code>contributions_baseplate.scad</code><br>
        Optional <code>contributions_baseplate.stl</code>
      </td>
      <td>
        <pre>Jan Feb Mar Apr May Jun Jul Aug
Sep Oct Nov Dec</pre>
      </td>
    </tr>
    <tr>
      <td><strong>Compact grid</strong></td>
      <td>
        <code>--colors 3</code><br>
        <code>--months-per-row 8</code>
      </td>
      <td>
        <code>contributions_color1.scad</code><br>
        <code>contributions_color2.scad</code><br>
        <code>contributions_color3.scad</code><br>
        Optional matching STLs<br>
        <code>contributions_baseplate.scad</code><br>
        Optional <code>contributions_baseplate.stl</code><br>
        Calendar exports relocate to <code>monthly-8x6/</code>
      </td>
      <td>
        <pre>Jan Feb Mar Apr May Jun Jul Aug
Sep Oct Nov Dec</pre>
      </td>
    </tr>
    <tr>
      <td><strong>Gridfinity layout only</strong></td>
      <td>
        <code>--colors 1</code><br>
        <code>--gridfinity-layouts</code><br>
        <code>--gridfinity-columns 6</code>
      </td>
      <td>
        Adds <code>stl/&lt;year&gt;/gridfinity_plate.scad</code><br>
        Optional <code>gridfinity_plate.stl</code>
      </td>
      <td>
        <pre>Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec</pre>
      </td>
    </tr>
    <tr>
      <td><strong>Gridfinity cubes + layout</strong></td>
      <td>
        <code>--colors 4</code><br>
        <code>--gridfinity-layouts</code><br>
        <code>--gridfinity-cubes</code><br>
        <code>--gridfinity-columns 4</code>
      </td>
      <td>
        Monthly <code>contrib_cube_MM.scad</code><br>
        Optional <code>contrib_cube_MM.stl</code><br>
        <code>gridfinity_plate.scad</code> / <code>.stl</code><br>
        Color files <code>_color1</code>…<code>_color4</code>
      </td>
      <td>
        <pre>Jan Feb Mar Apr May Jun Jul Aug
Sep Oct Nov Dec</pre>
      </td>
    </tr>
    <tr>
      <td><strong>Narrow layout with cubes</strong></td>
      <td>
        <code>--colors 5</code><br>
        <code>--months-per-row 6</code><br>
        <code>--gridfinity-layouts</code><br>
        <code>--gridfinity-cubes</code><br>
        <code>--gridfinity-columns 3</code>
      </td>
      <td>
        Same as previous row<br>
        Gridfinity plate shrinks to <code>3×4</code><br>
        Calendars relocate to <code>monthly-6x6/</code>
      </td>
      <td>
        <pre>Jan Feb Mar Apr May Jun
Jul Aug Sep Oct Nov Dec</pre>
      </td>
    </tr>
  </tbody>
</table>

**Legend**

- The monthly previews illustrate the top rows of the summary grid.
- When `--colors` is greater than one, `_colorN` SCAD/STL files replace the combined
  block export and any lingering single-color `<name>.scad`/`.stl` files are removed.
  `_baseplate` outputs always accompany color runs.
- `--gridfinity-cubes` removes stale `contrib_cube_MM` files (and any lingering STLs
  when `--stl` is absent) so directories stay aligned with the latest data.
- `--gridfinity-columns` only applies when `--gridfinity-layouts` is active. Values
  below one exit with a parser error before any files are written.
