/** 判断当前路径是否激活 */
export function isActivePath(currentPath: string, targetPath: string): boolean {
  return currentPath === targetPath ||
    (targetPath !== '/' && currentPath.startsWith(targetPath));
}
