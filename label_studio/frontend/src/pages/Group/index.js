
import React from 'react';
import { SidebarMenu } from '../../components/SidebarMenu/SidebarMenu';
import { GroupPage } from './GroupPage/GroupPage';
import { WebhookPage } from '../WebhookPage/WebhookPage';

const ALLOW_ORGANIZATION_WEBHOOKS = window.APP_SETTINGS.flags?.allow_organization_webhooks;


const MenuLayout = ({ children, ...routeProps }) => {
  let menuItems = [GroupPage];
  if (ALLOW_ORGANIZATION_WEBHOOKS){
    menuItems.push(
      WebhookPage,
    );
  }
  return (
    <SidebarMenu
      menuItems={menuItems}
      path={routeProps.match.url}
      children={children}
    />
  );
};

const groupPages = {};
if (ALLOW_ORGANIZATION_WEBHOOKS){
  groupPages[WebhookPage] = WebhookPage;
}

export const GroupsPage = {
  title: "Groups",
  path: "/group",
  exact: true,
  layout: MenuLayout,
  component: GroupPage,
  pages: groupPages,
};
