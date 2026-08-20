{{- define "gitshelves.name" -}}gitshelves{{- end }}
{{- define "gitshelves.fullname" -}}{{ .Release.Name }}-gitshelves{{- end }}
{{- define "gitshelves.labels" -}}
app.kubernetes.io/name: {{ include "gitshelves.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}
{{- define "gitshelves.selectorLabels" -}}
app.kubernetes.io/name: {{ include "gitshelves.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- define "gitshelves.image" -}}
{{- $tag := required "image.tag is required and must be immutable" .Values.image.tag -}}
{{- if or (eq $tag "latest") (eq $tag "main") (eq $tag "staging") (eq $tag "production") (not (regexMatch "^main-[0-9a-f]{7,40}$" $tag)) -}}{{ fail "image.tag must be immutable and shaped main-<7-to-40-lowercase-hex-sha>" }}{{- end -}}
{{ printf "%s:%s" .Values.image.repository $tag }}
{{- end }}
