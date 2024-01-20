import React from 'react';
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
import { GroupList } from "./GroupList";
import "./GroupPage.styl";
import { SelectedUser } from "./SelectedUser";
import { shallow } from "enzyme";


const GroupModal = ({ groupName, setGroupName, description, setDescription }) => {
  return (
    <Block name="group">
      <form className={"group-name"} onSubmit={e => { e.preventDefault(); onSubmit(); }} >
        <div className="field field--wide">
          <label htmlFor="group_name">Group Name</label>
          <input name="name" id="group_name" value={groupName} onChange={e => {e.preventDefault(); setGroupName(e.target.value)}} />
        </div>
        <Description style={{ width: '70%', marginTop: 16 }}>
          Enter your group's name
        </Description>
        <div className="field field--wide">
          <label htmlFor="group_description">Description</label>
          <textarea
            name="description"
            id="group_description"
            placeholder="Optional description of your group"
            rows="4"
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
        </div>
      </form>
    </Block>
  );
};

export const GroupPage = () => {
  const api = useAPI();
  const inviteModal = useRef();
  const groupModal = useRef();
  const config = useConfig();
  const [selectedUser, setSelectedUser] = useState(null);
  const [groupName, setGroupName] = useState()
  const [description, setDescription] = useState();

  const [link, setLink] = useState();

  const selectUser = useCallback((user) => {
    setSelectedUser(user);

    localStorage.setItem('selectedUser', user?.id);
  }, [setSelectedUser]);

  const groupModalProps = useCallback((groupName, setGroupName, description, setDescription) => ({
    title: "Create Group",
    style: { width: 640, height: 472 },
    body: () => (
      <GroupModal
        groupName={groupName}
        setGroupName={setGroupName}
        description={description}
        setDescription={setDescription}
      />
    ),
    footer: () => {

      return (
        <Space spread>
          <Space>

          </Space>
          <Space>
            <Button primary style={{ width: 170 }} onClick={onCreate} >
              Create
            </Button>
          </Space>
        </Space>
      );
    },
    bareFooter: true,

  }), [])

  const showGroupModal = useCallback(() => {
    groupModal.current = modal(groupModalProps(groupName, setGroupName, description, setDescription));
  }, [groupModalProps])

  const userBody = {}
    // first_name,
    // last_name,

  const onCreate = React.useCallback(async () => {
    // setWaitingStatus(true);
    const response = await api.callApi('me', {
    });
    // console.log(response.id);
    userBody.id = response.id
    userBody.first_name= response.first_name
    userBody.last_name = response.last_name
    userBody.username = response.username
    userBody.email = response.email


    // userBody.first_name = response

    // userbody = response.json()

    const response2 = await api.callApi('createGroup', {
      body: {
        name : "groupName",
        user : userBody,
        description : "description"
      },
    });
    // setGroupName(groupName)
    // console.log(groupName);

    // setWaitingStatus(false);

    // if (response !== null) {
    //   history.push(`/group/${response.id}/members`);
    // }
  }, []);




  const defaultSelected = useMemo(() => {
    return localStorage.getItem('selectedUser');
  }, []);

  useEffect(() => {
    groupModal.current?.update(groupModalProps())
  }, [])

  useEffect(() => {
    console.log(groupName);
    // setGroupName(groupName)
  }, [])

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
