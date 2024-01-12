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
// import "./PeopleInvitation.styl";
import { GroupList} from "./GroupList";
import "./GroupPage.styl";
import { SelectedUser } from "./SelectedUser";
import { shallow } from "enzyme";


const GroupModal = () => {
  return (
    <Block name="group">
      <Input
        style={{ width: '100%' }}
      />

      <Description style={{ width: '70%', marginTop: 16 }}>
        Enter your group's name
      </Description>
    </Block>
  );
};

export const GroupPage = () => {
  const api = useAPI();
  const inviteModal = useRef();
  const groupModal = useRef();
  const config = useConfig();
  const [selectedUser, setSelectedUser] = useState(null);

  const [link, setLink] = useState();

  const selectUser = useCallback((user) => {
    setSelectedUser(user);

    localStorage.setItem('selectedUser', user?.id);
  }, [setSelectedUser]);

  // const setInviteLink = useCallback((link) => {
  //   const hostname = config.hostname || location.origin;

  //   setLink(`${hostname}${link}`);
  // }, [config, setLink]);

  // const updateLink = useCallback(() => {
  //   api.callApi('resetInviteLink').then(({ invite_url }) => {
  //     setInviteLink(invite_url);
  //   });
  // }, [setInviteLink]);
  const groupModalProps = useCallback (() => ({
    title: "Create Group",
    style: { width: 640, height: 472 },
    body: () => (
      <GroupModal />
    ),
    footer: () => {

      return (
        <Space spread>
          <Space>

          </Space>
          <Space>
            <Button primary style={{ width: 170 }} >
              Create
            </Button>
          </Space>
        </Space>
      );
    },
    bareFooter: true,

  }),[])

  const showGroupModal = useCallback(() => {
    groupModal.current = modal(groupModalProps());
  }, [groupModalProps])


  // const inviteModalProps = useCallback((link) => ({
  //   title: "Invite people",
  //   style: { width: 640, height: 472 },
  //   body: () => (
  //     <InvitationModal link={link} />
  //   ),
  //   footer: () => {
  //     const [copied, setCopied] = useState(false);

  //     const copyLink = useCallback(() => {
  //       setCopied(true);
  //       copyText(link);
  //       setTimeout(() => setCopied(false), 1500);
  //     }, []);

  //     return (
  //       <Space spread>
  //         <Space>
  //           <Button style={{ width: 170 }} onClick={() => updateLink()}>
  //             Reset Link
  //           </Button>
  //         </Space>
  //         <Space>
  //           <Button primary style={{ width: 170 }} onClick={copyLink}>
  //             {copied ? "Copied!" : "Copy link"}
  //           </Button>
  //         </Space>
  //       </Space>
  //     );
  //   },
  //   bareFooter: true,
  // }), []);
    

  // const showInvitationModal = useCallback(() => {
  //   inviteModal.current = modal(inviteModalProps(link));
  // }, [inviteModalProps, link]);

  const defaultSelected = useMemo(() => {
    return localStorage.getItem('selectedUser');
  }, []);

  useEffect(() => {
    groupModal.current?.update(groupModalProps())
  }, [])

  // useEffect(() => {
  //   api.callApi("inviteLink").then(({ invite_url }) => {
  //     setInviteLink(invite_url);
  //   });
  // }, []);

  // useEffect(() => {
  //   inviteModal.current?.update(inviteModalProps(link));
  // }, [link]);

  return (
    <Block name="group">
      <Elem name="controls">
        <Space spread>
          <Space></Space>

          <Space>
            <Button icon={<LsPlus />} primary onClick={showGroupModal}>
              Create Group
            </Button>
          </Space>
        </Space>
      </Elem>
      <Elem name="content">
        <GroupList
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
          <HeidiTips collection="groupsPage" />
        )}
      </Elem>
    </Block>
  );
};

GroupPage.title = "Group";
GroupPage.path = "/";
