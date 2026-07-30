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
