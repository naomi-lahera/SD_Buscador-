import React, { useState } from 'react';
import { UploadOutlined, UserOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { Layout, Menu, theme } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { message, Upload } from 'antd';
import { AppstoreOutlined, BarsOutlined } from '@ant-design/icons';
import { Segmented } from 'antd';
import { Input } from 'antd';
import './App.css';

const { Search } = Input;

const { Header, Content, Footer, Sider } = Layout;

// const items = [UserOutlined, VideoCameraOutlined, UploadOutlined, UserOutlined].map(
//   (icon, index) => ({
//     key: String(index + 1),
//     icon: React.createElement(icon),
//     label: `nav ${index + 1}`,
//   }),
// );

const { TextArea } = Input;
const { Dragger } = Upload;

const props: UploadProps = {
  name: 'file',
  multiple: true,
  action: 'https://660d2bd96ddfa2943b33731c.mockapi.io/api/upload',
  onChange(info) {
    const { status } = info.file;
    if (status !== 'uploading') {
      console.log(info.file, info.fileList);
    }
    if (status === 'done') {
      message.success(`${info.file.name} file uploaded successfully.`);
    } else if (status === 'error') {
      message.error(`${info.file.name} file upload failed.`);
    }
  },
  onDrop(e) {
    console.log('Dropped files', e.dataTransfer.files);
  },
};

const App: React.FC = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();
  const [value, setValue] = useState('');

  return (
    <Layout className='layout'>
      <Header className='nav-header' style={{ padding: 0, background: colorBgContainer }}>
          <div className='header'>
          <Segmented
            options={[
              { label: 'Summary', value: 'List', icon: <BarsOutlined /> },
              { label: 'Docs', value: 'Kanban', icon: <AppstoreOutlined /> },
            ]}
          />
          </div>
        </Header>
      <Layout>
      <Sider style={{ background: '#FFF'}}
        className='left-sider'
        breakpoint="lg"
        collapsedWidth="0"
        onBreakpoint={(broken) => {
          console.log(broken);
        }}
        onCollapse={(collapsed, type) => {
          console.log(collapsed, type);
        }}
      >
        {/* <div className="demo-logo-vertical" /> */}
        {/* <Menu theme="dark" mode="inline" defaultSelectedKeys={['4']} items={items} /> */}
        <Dragger {...props} className='icon-container'>
            <InboxOutlined className='upload-drag-icon' style={{ fontSize: '50px'}}/>
          <p className="upload-text">Click or drag file to this area to upload</p>
        </Dragger>
      </Sider>

        <Content 
          className='container-query-result'
          style={{ margin: '10px 16px 0' }}>
          <div
            style={{
              marginTop: 0,
              padding: 24,
              height: 493,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <p 
              className='text-container'
              >


              </p>
            <Search placeholder="input search loading default" loading />
            <TextArea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Controlled autosize"
              autoSize={{ minRows: 3, maxRows: 5 }}
            />
          </div>
        </Content>
      </Layout>
      <Footer style={{ textAlign: 'center', fontSize :'15px' }}>
          Created by nao_lahera and cyberboy  ©{new Date().getFullYear()}
      </Footer>
    </Layout>
  );
};

export default App;

