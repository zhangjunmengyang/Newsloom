"use client";

import { useState, useEffect, useMemo } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Save, FileText, Settings as SettingsIcon, Database, Palette, Layout, Search } from "lucide-react";
import { fetchSettings, updateSetting, fetchSources, toggleSource, Source, fetchTemplates, updateTemplate, Template } from "@/lib/api";
import { useTheme } from "@/lib/theme";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("report");
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [sources, setSources] = useState<Source[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [currentTemplate, setCurrentTemplate] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [templateSearchQuery, setTemplateSearchQuery] = useState("");
  const { theme, setTheme, themes } = useTheme();

  // Filter and group templates
  const filteredAndGroupedTemplates = useMemo(() => {
    let filtered = templates.filter(template => 
      template.name.toLowerCase().includes(templateSearchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(templateSearchQuery.toLowerCase())
    );

    // Group by first letter of name for better organization
    const grouped = filtered.reduce((groups, template) => {
      const firstLetter = template.name.charAt(0).toUpperCase();
      if (!groups[firstLetter]) {
        groups[firstLetter] = [];
      }
      groups[firstLetter].push(template);
      return groups;
    }, {} as Record<string, Template[]>);

    // Sort groups by letter and templates within groups
    const sortedGroups: Record<string, Template[]> = {};
    Object.keys(grouped).sort().forEach(letter => {
      sortedGroups[letter] = grouped[letter].sort((a, b) => a.name.localeCompare(b.name));
    });

    return sortedGroups;
  }, [templates, templateSearchQuery]);

  // Local state for form fields
  const [template, setTemplate] = useState("newsletter");
  const [exportFormats, setExportFormats] = useState({
    pdf: true,
    html: true,
    markdown: false,
  });
  const [titlePrefix, setTitlePrefix] = useState("");
  const [pipelineLayers, setPipelineLayers] = useState({
    fetch: true,
    rank: true,
    analyze: true,
    generate: true,
  });
  const [model, setModel] = useState("gpt-4");

  useEffect(() => {
    const loadData = async () => {
      try {
        const [settingsData, sourcesData, templatesData] = await Promise.all([
          fetchSettings(),
          fetchSources(),
          fetchTemplates(),
        ]);
        setSettings(settingsData);
        setSources(sourcesData);
        setTemplates(templatesData);

        // Populate form fields from settings
        if (settingsData.template) setTemplate(settingsData.template);
        if (settingsData["report.template"]) setCurrentTemplate(settingsData["report.template"]);
        if (settingsData.export_formats) setExportFormats(settingsData.export_formats);
        if (settingsData.title_prefix) setTitlePrefix(settingsData.title_prefix);
        if (settingsData.pipeline_layers) setPipelineLayers(settingsData.pipeline_layers);
        if (settingsData.model) setModel(settingsData.model);
      } catch (error) {
        console.error("Failed to fetch settings:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      await Promise.all([
        updateSetting("template", template),
        updateSetting("export_formats", exportFormats),
        updateSetting("title_prefix", titlePrefix),
        updateSetting("pipeline_layers", pipelineLayers),
        updateSetting("model", model),
      ]);
    } catch (error) {
      console.error("Failed to save settings:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleToggleSource = async (id: number) => {
    try {
      await toggleSource(id);
      setSources(sources.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
    } catch (error) {
      console.error("Failed to toggle source:", error);
    }
  };

  const handleSelectTemplate = async (templateName: string) => {
    try {
      setLoadingTemplates(true);
      await updateTemplate(templateName);
      setCurrentTemplate(templateName);
      setTemplate(templateName); // Also update the local template state for the Report Generation tab
    } catch (error) {
      console.error("Failed to update template:", error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const tabs = [
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "templates", label: "Report Templates", icon: Layout },
    { id: "report", label: "Report Generation", icon: FileText },
    { id: "pipeline", label: "Pipeline Config", icon: SettingsIcon },
    { id: "sources", label: "Sources Overview", icon: Database },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Settings" />
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Settings</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Configure your Newsloom preferences and pipeline settings
              </p>
            </div>
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-border">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                    activeTab === tab.id
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab Content */}
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading settings...</p>
            </div>
          ) : (
            <>
              {/* Templates Tab */}
              {activeTab === "templates" && (
                <Card>
                  <CardHeader>
                    <CardTitle>Report Templates</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Choose from available report templates. Each template has a different layout and style.
                    </p>
                  </CardHeader>
                  <CardContent>
                    {loadingTemplates && (
                      <div className="text-center py-4">
                        <p className="text-sm text-muted-foreground">Updating template...</p>
                      </div>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {templates.map((template) => (
                        <button
                          key={template.name}
                          onClick={() => handleSelectTemplate(template.name)}
                          disabled={loadingTemplates}
                          className={`relative p-4 rounded-lg border-2 transition-all hover:scale-105 text-left ${
                            currentTemplate === template.name
                              ? 'border-primary shadow-lg'
                              : 'border-border hover:border-primary/50'
                          }`}
                        >
                          {/* Active indicator */}
                          {currentTemplate === template.name && (
                            <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-primary animate-pulse" />
                          )}

                          {/* Template preview placeholder */}
                          <div className="w-full h-32 bg-gradient-to-b from-card to-muted rounded-md border border-border mb-3 flex items-center justify-center">
                            <Layout className="h-8 w-8 text-muted-foreground" />
                          </div>

                          {/* Template info */}
                          <div>
                            <div className="font-semibold text-sm mb-1">{template.name}</div>
                            <div className="text-xs text-muted-foreground mb-2">
                              {template.description}
                            </div>
                            
                            {/* Theme badge */}
                            <div className="flex items-center gap-1 mb-2">
                              <span className="inline-flex items-center px-2 py-1 rounded-md bg-secondary text-xs font-medium">
                                {template.theme}
                              </span>
                            </div>

                            {/* Features */}
                            {template.features && template.features.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {template.features.map((feature, i) => (
                                  <span
                                    key={i}
                                    className="inline-flex items-center px-2 py-0.5 rounded-md bg-primary/10 text-xs text-primary"
                                  >
                                    {feature}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                    {templates.length === 0 && !loading && (
                      <div className="text-center py-8">
                        <Layout className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                        <p className="text-sm text-muted-foreground">No templates available</p>
                      </div>
                    )}
                    <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground">
                        <strong>Current template:</strong> {currentTemplate || "None selected"} 
                        {currentTemplate && " - Changes apply to future report generations."}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Appearance Tab */}
              {activeTab === "appearance" && (
                <Card>
                  <CardHeader>
                    <CardTitle>Dashboard Theme</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {themes.map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setTheme(t.id)}
                          className={`relative p-4 rounded-lg border-2 transition-all hover:scale-105 ${
                            theme === t.id
                              ? 'border-primary shadow-lg'
                              : 'border-border hover:border-primary/50'
                          }`}
                        >
                          {/* Active indicator */}
                          {theme === t.id && (
                            <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-primary animate-pulse" />
                          )}

                          {/* Color preview */}
                          <div className="flex gap-2 mb-3">
                            <div
                              className="w-16 h-16 rounded-md border border-border"
                              style={{ backgroundColor: t.preview.background }}
                            />
                            <div className="flex flex-col gap-2 flex-1">
                              <div
                                className="h-7 rounded-md"
                                style={{ backgroundColor: t.preview.primary }}
                              />
                              <div
                                className="h-7 rounded-md"
                                style={{ backgroundColor: t.preview.secondary }}
                              />
                            </div>
                          </div>

                          {/* Theme info */}
                          <div className="text-left">
                            <div className="font-semibold text-sm mb-1">{t.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {t.description}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground mt-4">
                      Theme changes are saved automatically and apply instantly across all pages.
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Report Generation Tab */}
              {activeTab === "report" && (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Template Selection</CardTitle>
                      <p className="text-sm text-muted-foreground">
                        Choose from {templates.length} available report templates. Changes apply to future report generations.
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {/* Search Box */}
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder="Search templates..."
                            value={templateSearchQuery}
                            onChange={(e) => setTemplateSearchQuery(e.target.value)}
                            className="pl-10"
                          />
                        </div>

                        {loadingTemplates && (
                          <div className="text-center py-4">
                            <p className="text-sm text-muted-foreground">Updating template...</p>
                          </div>
                        )}

                        {/* Template Grid */}
                        <div className="space-y-6">
                          {Object.entries(filteredAndGroupedTemplates).map(([letter, groupTemplates]) => (
                            <div key={letter}>
                              <h4 className="text-sm font-medium text-muted-foreground mb-3 sticky top-0 bg-background/80 backdrop-blur-sm py-1">
                                {letter}
                              </h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {groupTemplates.map((template) => (
                                  <button
                                    key={template.name}
                                    onClick={() => handleSelectTemplate(template.name)}
                                    disabled={loadingTemplates}
                                    className={`relative p-4 rounded-lg border-2 transition-all hover:scale-105 text-left group ${
                                      currentTemplate === template.name
                                        ? 'border-primary shadow-lg bg-primary/5'
                                        : 'border-border hover:border-primary/50'
                                    }`}
                                  >
                                    {/* Active indicator */}
                                    {currentTemplate === template.name && (
                                      <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-primary animate-pulse" />
                                    )}

                                    {/* Template preview with color */}
                                    <div className={`w-full h-24 rounded-md border border-border mb-3 flex items-center justify-center ${
                                      template.theme === 'dark' 
                                        ? 'bg-gradient-to-br from-slate-900 to-slate-700'
                                        : template.theme === 'blue'
                                        ? 'bg-gradient-to-br from-blue-500 to-blue-700'
                                        : template.theme === 'green'
                                        ? 'bg-gradient-to-br from-green-500 to-green-700'
                                        : template.theme === 'red'
                                        ? 'bg-gradient-to-br from-red-500 to-red-700'
                                        : template.theme === 'orange'
                                        ? 'bg-gradient-to-br from-orange-500 to-orange-700'
                                        : template.theme === 'purple'
                                        ? 'bg-gradient-to-br from-purple-500 to-purple-700'
                                        : 'bg-gradient-to-br from-card to-muted'
                                    }`}>
                                      <Layout className={`h-6 w-6 ${
                                        template.theme === 'dark' || template.theme === 'blue' || template.theme === 'green' || 
                                        template.theme === 'red' || template.theme === 'orange' || template.theme === 'purple'
                                          ? 'text-white'
                                          : 'text-muted-foreground'
                                      }`} />
                                    </div>

                                    {/* Template info */}
                                    <div>
                                      <div className="font-semibold text-sm mb-1 capitalize">
                                        {template.name.replace(/-/g, ' ')}
                                      </div>
                                      <div className="text-xs text-muted-foreground mb-2 h-8 overflow-hidden">
                                        {template.description}
                                      </div>
                                      
                                      {/* Theme badge */}
                                      <div className="flex items-center gap-1 mb-2">
                                        <span className="inline-flex items-center px-2 py-1 rounded-md bg-secondary text-xs font-medium">
                                          {template.theme}
                                        </span>
                                      </div>

                                      {/* Features */}
                                      {template.features && template.features.length > 0 && (
                                        <div className="flex flex-wrap gap-1">
                                          {template.features.slice(0, 2).map((feature, i) => (
                                            <span
                                              key={i}
                                              className="inline-flex items-center px-2 py-0.5 rounded-md bg-primary/10 text-xs text-primary"
                                            >
                                              {feature}
                                            </span>
                                          ))}
                                          {template.features.length > 2 && (
                                            <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-muted text-xs text-muted-foreground">
                                              +{template.features.length - 2}
                                            </span>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  </button>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>

                        {Object.keys(filteredAndGroupedTemplates).length === 0 && !loading && templateSearchQuery && (
                          <div className="text-center py-8">
                            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                            <p className="text-sm text-muted-foreground">No templates found matching "{templateSearchQuery}"</p>
                          </div>
                        )}

                        {templates.length === 0 && !loading && (
                          <div className="text-center py-8">
                            <Layout className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                            <p className="text-sm text-muted-foreground">No templates available</p>
                          </div>
                        )}

                        {/* Current selection status */}
                        <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                          <p className="text-xs text-muted-foreground">
                            <strong>Current template:</strong> {currentTemplate ? (
                              <span className="capitalize">{currentTemplate.replace(/-/g, ' ')}</span>
                            ) : "None selected"}
                            {currentTemplate && " - Changes apply to future report generations."}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Export Formats</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="pdf" className="flex-1">
                            <div className="font-medium">PDF Export</div>
                            <div className="text-xs text-muted-foreground">
                              Generate print-ready PDF files
                            </div>
                          </Label>
                          <Checkbox
                            id="pdf"
                            checked={exportFormats.pdf}
                            onCheckedChange={(checked) =>
                              setExportFormats({ ...exportFormats, pdf: !!checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="html" className="flex-1">
                            <div className="font-medium">HTML Export</div>
                            <div className="text-xs text-muted-foreground">
                              Generate web-ready HTML files
                            </div>
                          </Label>
                          <Checkbox
                            id="html"
                            checked={exportFormats.html}
                            onCheckedChange={(checked) =>
                              setExportFormats({ ...exportFormats, html: !!checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="markdown" className="flex-1">
                            <div className="font-medium">Markdown Export</div>
                            <div className="text-xs text-muted-foreground">
                              Keep raw markdown source
                            </div>
                          </Label>
                          <Checkbox
                            id="markdown"
                            checked={exportFormats.markdown}
                            onCheckedChange={(checked) =>
                              setExportFormats({ ...exportFormats, markdown: !!checked })
                            }
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Report Title</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <Label htmlFor="titlePrefix">Title Prefix</Label>
                        <Input
                          id="titlePrefix"
                          placeholder="e.g., Daily Intelligence Brief"
                          value={titlePrefix}
                          onChange={(e) => setTitlePrefix(e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">
                          This prefix will be added to all generated reports
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Pipeline Config Tab */}
              {activeTab === "pipeline" && (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Pipeline Layers</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="fetch" className="flex-1">
                            <div className="font-medium">Fetch Layer</div>
                            <div className="text-xs text-muted-foreground">
                              Collect articles from all sources
                            </div>
                          </Label>
                          <Checkbox
                            id="fetch"
                            checked={pipelineLayers.fetch}
                            onCheckedChange={(checked) =>
                              setPipelineLayers({ ...pipelineLayers, fetch: !!checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="rank" className="flex-1">
                            <div className="font-medium">Rank Layer</div>
                            <div className="text-xs text-muted-foreground">
                              Score and prioritize articles
                            </div>
                          </Label>
                          <Checkbox
                            id="rank"
                            checked={pipelineLayers.rank}
                            onCheckedChange={(checked) =>
                              setPipelineLayers({ ...pipelineLayers, rank: !!checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="analyze" className="flex-1">
                            <div className="font-medium">Analyze Layer</div>
                            <div className="text-xs text-muted-foreground">
                              Extract insights and summaries
                            </div>
                          </Label>
                          <Checkbox
                            id="analyze"
                            checked={pipelineLayers.analyze}
                            onCheckedChange={(checked) =>
                              setPipelineLayers({ ...pipelineLayers, analyze: !!checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="generate" className="flex-1">
                            <div className="font-medium">Generate Layer</div>
                            <div className="text-xs text-muted-foreground">
                              Create final report output
                            </div>
                          </Label>
                          <Checkbox
                            id="generate"
                            checked={pipelineLayers.generate}
                            onCheckedChange={(checked) =>
                              setPipelineLayers({ ...pipelineLayers, generate: !!checked })
                            }
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>AI Model</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <Label htmlFor="model">Language Model</Label>
                        <Select value={model} onValueChange={setModel}>
                          <SelectTrigger id="model">
                            <SelectValue placeholder="Select model" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                            <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                            <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          Choose the AI model for analysis and generation
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Sources Overview Tab */}
              {activeTab === "sources" && (
                <Card>
                  <CardHeader>
                    <CardTitle>Sources Quick Toggle</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {sources.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No sources configured
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Channel</TableHead>
                            <TableHead className="text-right">Enabled</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {sources.map((source) => (
                            <TableRow key={source.id}>
                              <TableCell className="font-medium">{source.name}</TableCell>
                              <TableCell className="text-muted-foreground text-sm">
                                {source.source_type}
                              </TableCell>
                              <TableCell className="text-muted-foreground text-sm">
                                {source.channel}
                              </TableCell>
                              <TableCell className="text-right">
                                <Switch
                                  checked={source.enabled}
                                  onCheckedChange={() => handleToggleSource(source.id)}
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
