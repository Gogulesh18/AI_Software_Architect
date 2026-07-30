import { ClassNode, FunctionNode, GenericNode, TableNode } from "./nodes";

// Split out from nodes.tsx: a file mixing component exports with a plain
// object export defeats React Fast Refresh (react-refresh/only-export-components).
export const nodeTypes = {
  fileNode: GenericNode,
  folderNode: GenericNode,
  packageNode: GenericNode,
  componentNode: GenericNode,
  clientNode: GenericNode,
  serviceNode: GenericNode,
  databaseNode: GenericNode,
  processNode: GenericNode,
  appNode: GenericNode,
  participantNode: GenericNode,
  endpointNode: GenericNode,
  functionNode: FunctionNode,
  classNode: ClassNode,
  tableNode: TableNode,
};
