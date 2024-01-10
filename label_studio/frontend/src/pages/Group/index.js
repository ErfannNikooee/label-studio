
import React from 'react';
import { SidebarMenu } from '../../components/SidebarMenu/SidebarMenu';
import { PeoplePage } from './PeoplePage/PeoplePage';
import { WebhookPage } from '../WebhookPage/WebhookPage';

const ALLOW_ORGANIZATION_WEBHOOKS = window.APP_SETTINGS.flags?.allow_organization_webhooks;


const MenuLayout = ({ children, ...routeProps }) => {
  let menuItems = [PeoplePage];
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

export const GroupPage = {
  title: "Groups",
  path: "/group",
  exact: true,
  layout: MenuLayout,
  component: PeoplePage,
  pages: groupPages,
};
