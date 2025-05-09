from bundlewrap.items import Item, ItemStatus
from bundlewrap.exceptions import BundleError
from bundlewrap.utils.text import force_text, mark_for_translation as _
from bundlewrap.utils.remote import PathInfo
import types
from shlex import quote


class Download(Item):
    """
    Download a file and verify its Hash.
    """
    BUNDLE_ATTRIBUTE_NAME = "downloads"
    NEEDS_STATIC = [
        "pkg_apt:",
        "pkg_pacman:",
        "pkg_yum:",
        "pkg_zypper:",
    ]
    ITEM_ATTRIBUTES = {
        'url': "",
        'sha256': "",
        'sha512': "",
        'verifySSL': True,
        'owner': "root",
        'group': "root",
        'mode': "0644",
    }
    ITEM_TYPE_NAME = "download"
    REQUIRED_ATTRIBUTES = ['url']

    def __repr__(self):
        return "<Download name:{}>".format(self.name)

    def get_hash_type(self):
        if self.attributes.get('sha512', None):
            return 'sha512'
        if self.attributes.get('sha256', None):
            return 'sha256'

        raise BundleError(_(
            "at least one hash must be set on {item} in bundle '{bundle}'"
        ).format(
            bundle=bundle.name,
            item=item_id,
        ))

    def __hash_remote_file(self, filename, hash_type):
        path_info = PathInfo(self.node, filename)
        if not path_info.is_file:
            return None

        if hasattr(path_info, hash_type):
            if hash_type == 'sha256':
                return path_info.sha256
            elif hash_type == 'sha512':
                return path_info.sha512
            else:
                raise ValueError(_('unknown hash type {}'.format(hash_type)))

        else:
            """"pending pr so do it manualy"""
            if self.node.os == 'macos':
                result = self.node.run("shasum -a {} -- {}".format(hash_type[3:], quote(filename)))
            elif self.node.os in self.node.OS_FAMILY_BSD:
                result = self.node.run("{} -q -- {}".format(hash_type, quote(filename)))
            else:
                result = self.node.run("{}sum -- {}".format(hash_type, quote(filename)))
            return force_text(result.stdout).strip().split()[0]

    def fix(self, status):
        if status.must_be_deleted:
            # Not possible
            pass
        else:
            # download file
            self.node.run("curl -L {verify}-s -o {file} -- {url}".format(
                verify="" if self.attributes.get('verifySSL', True) else "-k ",
                file=quote(self.name),
                url=quote(self.attributes['url'])
            ))

            # check hash
            hash = self.__hash_remote_file(self.name, self.get_hash_type())

            if hash != self.attributes.get(self.get_hash_type()):
                # unlink file
                self.node.run("rm -rf -- {}".format(quote(self.name)))

                return False

            # Set owner
            self.node.run('chown {owner}:{group} {file}'.format(
                owner=self.attributes['owner'],
                group=self.attributes['group'],
                file=quote(self.name),
            ))

            # Set mode
            self.node.run('chmod {mode} {file}'.format(
                mode=self.attributes['mode'],
                file=quote(self.name),
            ))

    def cdict(self):
        """This is how the world should be"""
        cdict = {
            'type': 'download',
            'hash': self.attributes[self.get_hash_type()],
            'owner': self.attributes['owner'],
            'group': self.attributes['group'],
            'mode': self.attributes['mode'],
        }

        return cdict

    def sdict(self):
        """This is how the world is right now"""
        path_info = PathInfo(self.node, self.name)
        if not path_info.exists:
            return None
        else:
            sdict = {
                'type': 'download',
                'hash': self.__hash_remote_file(self.name, self.get_hash_type()),
                'owner': path_info.owner,
                'group': path_info.group,
                'mode': path_info.mode,
            }

        return sdict

    @classmethod
    def validate_attributes(cls, bundle, item_id, attributes):
        if attributes.get('sha256', None) is None and attributes.get('sha512', None) is None:
            raise BundleError(_(
                "at least one hash must be set on {item} in bundle '{bundle}'"
            ).format(
                bundle=bundle.name,
                item=item_id,
            ))

    def get_auto_deps(self, items):
        deps = []
        for item in items:
            # debian TODO: add other package manager
            if item.ITEM_TYPE_NAME == 'pkg_apt' and item.name == 'curl':
                deps.append(item.id)
        return deps
