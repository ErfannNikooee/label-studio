import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LsPlus } from "../../../assets/icons";
import { Button } from "../../../components";
import { Description } from "../../../components/Description/Description";
import { Input } from "../../../components/Form";
import { HeidiTips } from "../../../components/HeidiTips/HeidiTips";
import { modal } from "../../../components/Modal/Modal";
import { Space } from "../../../components/Space/Space";
import { useAPI } from "../../../providers/ApiProvider";
import { useConfig } from "../../../providers/ConfigProvider";
import { Block, Elem } from "../../../utils/bem";
import { FF_LSDV_E_297, isFF } from "../../../utils/feature-flags";
import { copyText } from "../../../utils/helpers";
import "./PeopleInvitation.styl";
import { PeopleList } from "./PeopleList";
import "./PeoplePage.styl";
import { SelectedUser } from "./SelectedUser";

const InvitationModal = ({ link }) => {
  return (
    <Block name="invite">
      <Input
        value={link}
        style={{ width: '100%' }}
        readOnly
      />

      <Description style={{ width: '70%', marginTop: 16 }}>
        Invite people to join your Label Studio instance. People that you invite have full access to all of your projects. <a href="https://labelstud.io/guide/signup.html">Learn more</a>.
      </Description>
    </Block>
  );
};


const OrganizationModal = ({ orgName, setOrgName }) => {
  const memoizedSetOrganizationName = useMemo(() => setOrgName, [setOrgName]);

  return (
    <Block name="organization">
      <form className={"organization-name"} onSubmit={e => { e.preventDefault(); onSubmit(); }} >
        <div className="field field--wide">
          <label htmlFor="organization">Organization Name</label>
          <input name="name" id="organization_name" value={orgName} onChange={(e) => memoizedSetOrganizationName(e.target.value)} />
        </div>
        <Description style={{ width: '70%', marginTop: 16 }}>
          Enter the organization's name
        </Description>
      </form>
    </Block>
  );
};


export const PeoplePage = () => {
  const api = useAPI();
  const inviteModal = useRef();
  const organizationModal = useRef();
  const config = useConfig();
  const [selectedUser, setSelectedUser] = useState(null);
  const [orgName, setOrgName] = useState()

  const [link, setLink] = useState();

  const selectUser = useCallback((user) => {
    setSelectedUser(user);

    localStorage.setItem('selectedUser', user?.id);
  }, [setSelectedUser]);

  const setInviteLink = useCallback((link) => {
    const hostname = config.hostname || location.origin;

    setLink(`${hostname}${link}`);
  }, [config, setLink]);

  const updateLink = useCallback(() => {
    api.callApi('resetInviteLink').then(({ invite_url }) => {
      setInviteLink(invite_url);
    });
  }, [setInviteLink]);

  const inviteModalProps = useCallback((link) => ({
    title: "Invite people",
    style: { width: 640, height: 472 },
    body: () => (
      <InvitationModal link={link} />
    ),
    footer: () => {
      const [copied, setCopied] = useState(false);

      const copyLink = useCallback(() => {
        setCopied(true);
        copyText(link);
        setTimeout(() => setCopied(false), 1500);
      }, []);

      return (
        <Space spread>
          <Space>
            <Button style={{ width: 170 }} onClick={() => updateLink()}>
              Reset Link
            </Button>
          </Space>
          <Space>
            <Button primary style={{ width: 170 }} onClick={copyLink}>
              {copied ? "Copied!" : "Copy link"}
            </Button>
          </Space>
        </Space>
      );
    },
    bareFooter: true,
  }), []);

  const organizationModalProps = useCallback(() => {
    organizationModal.current = modal({
      title: "Create Organization",
      style: { width: 640, height: 472 },
      body: () => (
        <OrganizationModal
          orgName={orgName}
          setOrgName={setOrgName}
          // onSubmit={onCreate}
        />
      ),
      footer: () => (
        <Space spread>
          <Space></Space>
          <Space>
            <Button primary style={{ width: 170 }} >
              Create
            </Button>
          </Space>
        </Space>
      ),
      bareFooter: true,
    });
  }, []);

  const showInvitationModal = useCallback(() => {
    inviteModal.current = modal(inviteModalProps(link));
  }, [inviteModalProps, link]);

  const showOrganizationModal = useCallback(() => {
    organizationModal.current = modal(organizationModalProps(orgName,setOrgName))
  }, [orgName,setOrgName]);

  useEffect(() => {
    api.callApi("inviteLink").then(({ invite_url }) => {
      setInviteLink(invite_url);
    });
  }, []);

  useEffect(() => {
    inviteModal.current?.update(inviteModalProps(link));
  }, [link]);

  const defaultSelected = useMemo(() => {
    return localStorage.getItem('selectedUser');
  }, []);

  useEffect(() => {
    organizationModal.current?.update(organizationModalProps())
  }, [organizationModalProps])

  return (
    <Block name="people">
      <Elem name="controls">
        <Space spread>
          <Space></Space>


          <Space>

            <Button icon={<LsPlus />} primary onClick={showInvitationModal}>
              Add People
            </Button>
            <Button icon={<LsPlus />} primary onClick={showOrganizationModal}>
              Create Organization
            </Button>
          </Space>
        </Space>
      </Elem>
      <Elem name="content">
        <PeopleList
          selectedUser={selectedUser}
          defaultSelected={defaultSelected}
          onSelect={(user) => selectUser(user)}
        />

        {selectedUser ? (
          <SelectedUser
            user={selectedUser}
            onClose={() => selectUser(null)}
          />
        ) : isFF(FF_LSDV_E_297) && (
          <HeidiTips collection="organizationPage" />
        )}
      </Elem>
    </Block>
  );
};

PeoplePage.title = "People";
PeoplePage.path = "/";
