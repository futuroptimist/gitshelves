{{- define "gitshelves.labels" -}}
app.kubernetes.io/name: gitshelves
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: gitshelves-{{ .Chart.Version }}
{{- end }}
{{- define "gitshelves.selectorLabels" -}}
app.kubernetes.io/name: gitshelves
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- define "gitshelves.validateTag" -}}
{{- $tag := required "image.tag is required and must be immutable" .Values.image.tag -}}
{{- if or (eq $tag "latest") (eq $tag "main") (eq $tag "staging") (eq $tag "production") (not (regexMatch "^[a-z0-9][a-z0-9._-]*-[0-9a-f]{7,40}$" $tag)) -}}
{{- fail "image.tag must be an immutable lowercase branch-SHA tag (for example main-0123456)" -}}
{{- end -}}
{{- end }}
