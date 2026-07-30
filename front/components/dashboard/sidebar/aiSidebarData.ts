export type SidebarConversation = {
  id: string;
  title: string;
  status: string;
  updatedAt: string;
  isActive?: boolean;
};

export type SidebarFile = {
  id: string;
  filename: string;
  meta: string;
};

export const sidebarConversations: SidebarConversation[] = [
  {
    id: "gl-anonymise",
    title: "Analyse GL anonymisé",
    status: "Structure Excel",
    updatedAt: "Maintenant",
    isActive: true,
  },
  {
    id: "tva-columns",
    title: "Contrôle colonnes TVA",
    status: "Qualité données",
    updatedAt: "Hier",
  },
  {
    id: "account-44585100",
    title: "Compte 44585100",
    status: "Écritures",
    updatedAt: "Lun.",
  },
  {
    id: "ras-suppliers",
    title: "Retenues fournisseurs",
    status: "Contrôle RAS",
    updatedAt: "12 juil.",
  },
  {
    id: "missing-tax-code",
    title: "Codes TVA manquants",
    status: "Anomalies",
    updatedAt: "8 juil.",
  },
  {
    id: "ledger-balance",
    title: "Équilibre du Grand Livre",
    status: "Cadrage",
    updatedAt: "2 juil.",
  },
];

export const sidebarFiles: SidebarFile[] = [
  {
    id: "gl-2500",
    filename: "GL_anonymise_2500.xlsx",
    meta: "2500 lignes",
  },
  {
    id: "gl-full",
    filename: "GL_anonymise.xlsx",
    meta: "Excel",
  },
];
